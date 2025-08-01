#!/bin/bash

set -euo pipefail

function cleanup() {
    cd "$1"
    
    # Replace specific names with company.databricks.com, user@company.com, user_name
    find . -type f -exec sed -i '' -E 's|e2[^[:space:]]*\.com|company.databricks.com|g' {} \;
    find . -type f -exec sed -i '' -E 's|[A-Za-z0-9._%+-]+@databricks\.com|user@company.com|g' {} \;
    find . -type f -exec sed -i '' -e "s|$CURRENT_USER_NAME|user_name|g" {} \;
    
    cd ..
}

function init_bundle() {
    local TEMPLATE_NAME="$1"
    local CONFIG_JSON="$2"
    
    # Extract project_name from JSON
    local PROJECT_NAME=$(echo "$CONFIG_JSON" | grep -o '"project_name"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
    
    # Use 'cli' if available, otherwise fall back to 'databricks'
    local CLI_CMD="databricks"
    if command -v cli >/dev/null 2>&1; then
        CLI_CMD="cli"
    fi
    
    echo
    echo "# $PROJECT_NAME"
    
    rm -rf "$PROJECT_NAME"
    echo "$CONFIG_JSON" > /tmp/config.json
    $CLI_CMD bundle init "$TEMPLATE_NAME" --config-file /tmp/config.json
    cleanup "$PROJECT_NAME"
}

# Check and extract the host from the databrickscfg file
if [ ! -f ~/.databrickscfg ]; then
    echo "Error: ~/.databrickscfg not found." >&2
    exit 1
fi

DATABRICKS_HOST=$(grep -A1 '\[DEFAULT\]' ~/.databrickscfg | grep 'host' | awk -F'=' '{print $2}' | xargs || true)
if [ ! "$DATABRICKS_HOST" ]; then
    echo "Error: expected ~/.databrickscfg file with a [DEFAULT] section with the first line of the form 'host=...'." >&2
    exit 1
fi

if [ -n "$1" ]; then 
    CURRENT_USER_NAME="$1"
else
    read -p "Enter the current user name (e.g., 'lennart_kats'): " CURRENT_USER_NAME
    read -p "Enter the current user name (e.g., 'lennart_kats'): " CURRENT_USER_NAME
    if [ ! "$CURRENT_USER_NAME" ]; then
        echo "Error: current user name is required." >&2
        exit 1
    fi
fi

cd $(dirname $0)/..

init_bundle "default-python" '{
    "project_name":     "default_python",
    "include_notebook": "yes",
    "include_dlt":      "yes",
    "include_python":   "yes",
    "serverless":       "yes"
}'

init_bundle "default-sql" '{
    "project_name":     "default_sql",
    "http_path":        "/sql/1.0/warehouses/abcdef1234567890",
    "default_catalog":  "catalog",
    "personal_schemas": "yes, automatically use a schema based on the current user name during development"
}'

init_bundle "dbt-sql" '{
    "project_name":     "dbt_sql",
    "http_path":        "/sql/1.0/warehouses/abcdef1234567890",
    "default_catalog":  "catalog",
    "personal_schemas": "yes, use a schema based on the current user name during development"
}'

init_bundle "lakeflow-pipelines" '{
    "project_name":     "lakeflow_pipelines_sql",
    "default_catalog":  "catalog",
    "personal_schemas": "yes",
    "language":         "sql"
}'


init_bundle "lakeflow-pipelines" '{
    "project_name":     "lakeflow_pipelines_python",
    "default_catalog":  "catalog",
    "personal_schemas": "yes",
    "language":         "python"
}'

cd contrib
(
    init_bundle "templates/data-engineering" '{
        "project_name":     "data_engineering",
        "default_catalog":  "catalog",
        "personal_schemas": "yes, use a schema based on the current user name during development"
    }'
)
cd ..