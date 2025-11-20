CREATE OR REFRESH STREAMING TABLE parsed_documents_structured
COMMENT 'Structured data extracted from document text using AI'
AS (
  SELECT
    path,
    ai_query(
      'databricks-claude-sonnet-4',
      concat(
        'Extract key information from this document and return as JSON. ',
        'Include: document_type, key_entities (names, organizations, locations), ',
        'dates, amounts, and a brief summary (max 100 words). ',
        'Document text: ',
        text
      ),
      returnType => 'STRING',
      modelParameters => named_struct(
        'max_tokens', 2000,
        'temperature', 0.1
      )
    ) AS extracted_json,
    parsed_at,
    current_timestamp() AS extraction_timestamp
  FROM STREAM(parsed_documents_text)
  WHERE text IS NOT NULL
    AND error_status IS NULL
    AND length(text) > 100
);
