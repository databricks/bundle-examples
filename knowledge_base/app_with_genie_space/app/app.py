import os

from databricks.sdk import WorkspaceClient
from flask import Flask, render_template, request

app = Flask(__name__)

w = WorkspaceClient()

# The space ID is injected by the "genie_space" resource declared in app.yml.
space_id = os.getenv("GENIE_SPACE_ID")


@app.route("/", methods=["GET", "POST"])
def home():
    question = None
    answer = None
    sql = None
    columns = []
    rows = []

    if request.method == "POST":
        question = request.form["question"]

        # Start a new conversation in the Genie space and wait for the answer.
        # Use w.genie.create_message_and_wait(...) to ask follow-up questions
        # in the same conversation.
        message = w.genie.start_conversation_and_wait(space_id, question)

        for attachment in message.attachments or []:
            # Genie answers either with plain text...
            if attachment.text:
                answer = attachment.text.content

            # ...or with a generated SQL query and its result set.
            if attachment.query:
                answer = attachment.query.description
                sql = attachment.query.query
                result = w.genie.get_message_attachment_query_result(
                    space_id,
                    message.conversation_id,
                    message.id,
                    attachment.attachment_id,
                )
                statement = result.statement_response
                columns = [column.name for column in statement.manifest.schema.columns]
                rows = statement.result.data_array or []

    return render_template(
        "index.html",
        question=question,
        answer=answer,
        sql=sql,
        columns=columns,
        rows=rows,
    )
