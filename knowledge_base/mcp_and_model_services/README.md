# MCP and model services

This Declarative Automation Bundles example defines an AI Gateway model service, a model provider service, and an MCP service in a Unity Catalog schema.
The model service routes chat requests to a Databricks foundation model. The model provider service connects to Anthropic with relayed authentication. The MCP service exposes the tools of an external MCP server.

For more information, see the [bundle resources documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/resources#model_services).

## Prerequisites

* Databricks CLI v1.20.0 or above, authenticated with OAuth (`databricks auth login`)
* `jq`
* A Unity Catalog catalog where you can create schemas
* A schema-level HTTP connection to an MCP server. See [Register an external MCP server](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service).

## Usage

1. Select a pay-per-token foundation model from the `system.ai` schema, for example `system.ai.databricks-claude-sonnet-4-6`.

2. Deploy the bundle. Replace the placeholders with your catalog, model, and connection:
   ```bash
   databricks bundle deploy --var catalog=<catalog> --var chat_model=<model> --var mcp_connection=<connection>
   ```

3. Send a chat request to the model service. The schema name is `<catalog>.dev_<your_user>_ai_services`:
   ```bash
   databricks api post /ai-gateway/mlflow/v1/chat/completions --json '{
     "model": "<catalog>.dev_<your_user>_ai_services.chat",
     "messages": [{"role": "user", "content": "What is Databricks?"}]
   }'
   ```

4. List the tools of the MCP service. The command gets the host and a token from the CLI:
   ```bash
   curl -X POST "$(databricks auth describe --output json | jq -r .details.host)/ai-gateway/mcp-services/<catalog>.dev_<your_user>_ai_services.docs" \
     -H "Authorization: Bearer $(databricks auth token | jq -r .access_token)" \
     -H "Accept: application/json, text/event-stream" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
   ```

5. Remove the services and the schema:
   ```bash
   databricks bundle destroy --var catalog=<catalog> --var chat_model=<model> --var mcp_connection=<connection>
   ```
