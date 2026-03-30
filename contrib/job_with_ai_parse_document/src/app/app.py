"""
Document Analyzer App
Upload a PDF, parse it with ai_parse_document, classify it with ai_classify,
and extract structured information with ai_query.
"""

import json
import os
import io
import time
import uuid

import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

st.set_page_config(page_title="Document Analyzer", layout="wide")

CATALOG = os.environ.get("CATALOG", "main")
SCHEMA = os.environ.get("SCHEMA", "default")
VOLUME = os.environ.get("VOLUME", "source_documents")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")

VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

DOCUMENT_TYPES = [
    "Invoice",
    "Contract",
    "Report",
    "Letter",
    "Resume",
    "Receipt",
    "Legal Document",
    "Technical Document",
    "Financial Statement",
    "Medical Record",
    "Insurance Claim",
    "Purchase Order",
    "Other",
]


# ---------------------------------------------------------------------------
# Workspace client (singleton)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_workspace_client():
    return WorkspaceClient()


# ---------------------------------------------------------------------------
# SQL execution via Statement Execution API (REST-based)
# ---------------------------------------------------------------------------
def run_query(query: str, timeout_seconds: int = 300) -> list[dict]:
    w = get_workspace_client()
    response = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=query,
        catalog=CATALOG,
        schema=SCHEMA,
        wait_timeout="0s",  # async — we poll ourselves
    )

    # Poll until done
    statement_id = response.statement_id
    deadline = time.time() + timeout_seconds
    while response.status and response.status.state in (
        StatementState.PENDING,
        StatementState.RUNNING,
    ):
        if time.time() > deadline:
            w.statement_execution.cancel_execution(statement_id)
            raise TimeoutError(f"Query timed out after {timeout_seconds}s")
        time.sleep(2)
        response = w.statement_execution.get_statement(statement_id)

    if response.status and response.status.state == StatementState.FAILED:
        error_msg = ""
        if response.status.error:
            error_msg = response.status.error.message or ""
        raise RuntimeError(f"Query failed: {error_msg}")

    if not response.result or not response.manifest:
        return []

    columns = [col.name for col in response.manifest.schema.columns]
    rows = []
    if response.result.data_array:
        for row_data in response.result.data_array:
            rows.append(dict(zip(columns, row_data)))
    return rows


# ---------------------------------------------------------------------------
# Upload file to volume
# ---------------------------------------------------------------------------
def upload_to_volume(file_bytes: bytes, filename: str) -> str:
    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    volume_file_path = f"{VOLUME_PATH}/{unique_name}"
    w = get_workspace_client()
    w.files.upload(volume_file_path, io.BytesIO(file_bytes), overwrite=True)
    return volume_file_path


# ---------------------------------------------------------------------------
# AI analysis queries
# ---------------------------------------------------------------------------
def parse_and_extract_text(volume_file_path: str) -> str:
    query = f"""
    SELECT cast(
        ai_parse_document(
            content,
            map('version', '2.0', 'descriptionElementTypes', '*')
        ) as STRING
    ) as parsed_json
    FROM read_files('{volume_file_path}')
    """
    rows = run_query(query)
    if not rows:
        raise RuntimeError("ai_parse_document returned no rows")

    raw = rows[0].get("parsed_json")
    if not raw:
        raise RuntimeError(
            f"ai_parse_document returned empty result. Row keys: {list(rows[0].keys())}"
        )

    parsed = json.loads(raw)
    elements = parsed.get("document", {}).get("elements", [])
    texts = [e.get("content", "") for e in elements if e.get("content")]
    return "\n\n".join(texts)


def classify_document(document_text: str) -> str:
    labels = ", ".join([f"'{t}'" for t in DOCUMENT_TYPES])
    escaped = document_text.replace("\\", "\\\\").replace("'", "\\'")
    truncated = escaped[:8000]
    query = f"""
    SELECT ai_classify(
        '{truncated}',
        ARRAY({labels})
    ) as document_type
    """
    rows = run_query(query)
    if rows and rows[0].get("document_type"):
        return rows[0]["document_type"]
    return "Unknown"


def summarize_document(document_text: str) -> str:
    escaped = document_text.replace("\\", "\\\\").replace("'", "\\'")
    truncated = escaped[:12000]
    query = f"""
    SELECT ai_query(
        'databricks-claude-sonnet-4',
        concat(
            'Extract key information from this document and return as JSON. ',
            'Include: document_type, key_entities (names, organizations, locations), ',
            'dates, amounts, and a brief summary (max 100 words). ',
            'Document text: ',
            '{truncated}'
        ),
        returnType => 'STRING',
        modelParameters => named_struct(
            'max_tokens', 2000,
            'temperature', 0.1
        )
    ) as summary
    """
    rows = run_query(query)
    if rows and rows[0].get("summary"):
        return rows[0]["summary"]
    return "{}"


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("Document Analyzer")
st.markdown("Upload a PDF document to analyze its contents using Databricks AI functions.")

# Verify SDK + warehouse connectivity on load
try:
    w = get_workspace_client()
    _me = w.current_user.me()
    if not WAREHOUSE_ID:
        st.error("DATABRICKS_WAREHOUSE_ID is not set.")
        st.stop()
except Exception as e:
    st.error(f"Failed to initialize Databricks SDK: {e}")
    st.stop()

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Upload a PDF document to analyze",
)

if uploaded_file:
    st.success(f"File uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

    if st.button("Analyze", type="primary", use_container_width=True):
        file_bytes = uploaded_file.read()

        with st.status("Analyzing document...", expanded=True) as status:
            # Step 1: Upload to volume
            st.write("Uploading document to volume...")
            try:
                volume_path = upload_to_volume(file_bytes, uploaded_file.name)
                st.write(f"Uploaded to `{volume_path}`")
            except Exception as e:
                st.error(f"Upload failed: {e}")
                st.stop()

            # Step 2: Parse and extract text
            st.write("Parsing document with `ai_parse_document`...")
            try:
                document_text = parse_and_extract_text(volume_path)
                if not document_text:
                    st.error("No text could be extracted from the document.")
                    st.stop()
                st.write(f"Extracted {len(document_text):,} characters of text")
            except Exception as e:
                st.error(f"Parsing failed: {e}")
                st.stop()

            # Step 3: Classify
            st.write("Classifying document with `ai_classify`...")
            try:
                doc_type = classify_document(document_text)
            except Exception as e:
                st.error(f"Classification failed: {e}")
                doc_type = "Unknown"

            # Step 4: Summarize
            st.write("Extracting information with `ai_query` (Claude)...")
            try:
                summary_raw = summarize_document(document_text)
            except Exception as e:
                st.error(f"Summary failed: {e}")
                summary_raw = "{}"

            status.update(label="Analysis complete!", state="complete", expanded=False)

        # -------------------------------------------------------------------
        # Results
        # -------------------------------------------------------------------
        st.markdown("---")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Document Type")
            st.metric(label="Classification", value=doc_type)

        with col2:
            st.subheader("AI Summary")
            # Strip markdown code fences if present
            cleaned = summary_raw.strip()
            if cleaned.startswith("```"):
                cleaned = "\n".join(cleaned.split("\n")[1:])
            if cleaned.endswith("```"):
                cleaned = "\n".join(cleaned.split("\n")[:-1])
            cleaned = cleaned.strip()
            try:
                summary_json = json.loads(cleaned)
                if isinstance(summary_json, dict) and "summary" in summary_json:
                    st.write(summary_json["summary"])
                else:
                    st.write(cleaned)
            except (json.JSONDecodeError, TypeError):
                st.write(cleaned)

        with st.expander("Extracted text"):
            st.text(document_text[:5000])
            if len(document_text) > 5000:
                st.caption(f"... truncated ({len(document_text):,} total characters)")

        with st.expander("Raw AI summary (JSON)"):
            st.code(summary_raw, language="json")
else:
    st.info("Upload a PDF file above to get started.")

st.markdown("---")
st.caption(
    "Powered by Databricks AI Functions: `ai_parse_document`, `ai_classify`, `ai_query`"
)
