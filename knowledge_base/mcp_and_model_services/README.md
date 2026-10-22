# MCP and model services

This Declarative Automation Bundles example defines an AI Gateway model service and an MCP service in a Unity Catalog schema.
The model service routes chat requests to a Databricks foundation model. The MCP service exposes the tools of an external MCP server.

For more information, see the [bundle resources documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/resources#model_services).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A Unity Catalog catalog where you can create schemas
* A schema-level HTTP connection to an MCP server. See [Register an external MCP server](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service).

## Usage

1. Deploy the bundle. Replace the values with your catalog and connection:
   ```bash
   databricks bundle deploy --var catalog=main --var mcp_connection=main.default.my_mcp_connection
   ```

2. Send a chat request to the model service. Use the schema name from `databricks bundle summary`:
   ```bash
   databricks api post /ai-gateway/mlflow/v1/chat/completions --json '{
     "model": "main.dev_<your_user>_ai_services.chat",
     "messages": [{"role": "user", "content": "What is Databricks?"}]
   }'
   ```

3. List the MCP tools. Get a token from `databricks auth token`:
   ```bash
   curl -X POST "https://<workspace-host>/ai-gateway/mcp-services/main.dev_<your_user>_ai_services.docs" \
     -H "Authorization: Bearer <token>" \
     -H "Accept: application/json, text/event-stream" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
   ```

4. Remove the services and the schema:
   ```bash
   databricks bundle destroy --var catalog=main --var mcp_connection=main.default.my_mcp_connection
   ```
