#!/bin/bash

################################################################################
# Azure Monitor DCE and DCR Setup Script
#
# This script creates Data Collection Endpoint (DCE) and Data Collection Rule (DCR)
# for sending Databricks telemetry to Azure Monitor.
#
# Resources created:
# - Data Collection Endpoint (DCE)
# - Custom tables (DatabricksMetrics_CL, DatabricksLogs_CL, DatabricksEvents_CL)
# - Data Collection Rule (DCR) with three streams
#
# Usage:
#   ./azure_setup.sh --resource-group <rg> --location <region> --workspace-name <name>
#
# Example:
#   ./azure_setup.sh \
#       --resource-group databricks-monitoring-rg \
#       --location "East US" \
#       --workspace-name databricks-monitoring-workspace
#
# Note: The script will create data collection rule "databricks-monitoring-dcr" and
# a public data collection endpoint "databricks-monitoring-dce". To override these values change the
# global variables $DCE_NAME and $DCR_NAME.
#
# Output:
#   - Azure Host Name (DCE hostname)
#   - Azure DCR Immutable ID
################################################################################

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# DCE and DCR names - modify these if needed
DCE_NAME="databricks-monitoring-dce"
DCR_NAME="databricks-monitoring-dcr"

# Function to show usage
usage() {
    cat << EOF
Usage: $0 --resource-group <rg> --location <region> --workspace-name <name>

Required arguments:
  --resource-group    Name of the existing Azure resource group
  --location          Azure region (e.g., 'East US', 'West Europe')
  --workspace-name    Name of the Log Analytics workspace

Optional arguments:
  --help              Show this help message

Example:
  $0 --resource-group databricks-monitoring-rg \\
     --location "East US" \\
     --workspace-name databricks-monitoring-workspace

Note: DCE and DCR names are set at the top of this script.
      Current values: DCE_NAME=$DCE_NAME, DCR_NAME=$DCR_NAME

For more information, see: README-third-party-monitoring.md
EOF
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        --location)
            LOCATION="$2"
            shift 2
            ;;
        --workspace-name)
            WORKSPACE_NAME="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$RESOURCE_GROUP" || -z "$LOCATION" || -z "$WORKSPACE_NAME" ]]; then
    echo "ERROR: Missing required arguments" >&2
    usage
fi

echo "Starting Azure Monitor DCE and DCR setup..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Workspace Name: $WORKSPACE_NAME"
echo "DCE Name: $DCE_NAME"
echo "DCR Name: $DCR_NAME"
echo ""

# Step 1: Create Data Collection Endpoint
echo "[1/2] Creating Data Collection Endpoint..."
az monitor data-collection endpoint create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DCE_NAME" \
    --location "$LOCATION" \
    --public-network-access "Enabled"

DCE_ENDPOINT=$(az monitor data-collection endpoint show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DCE_NAME" \
    --query "logsIngestion.endpoint" -o tsv)

HOST_NAME="${DCE_ENDPOINT#https://}"

# Step 2: Create Custom Tables and Data Collection Rule
echo "[2/2] Creating custom tables and data collection rule..."

# Define table schemas in column_name=column_type format
declare -A TABLE_SCHEMAS
TABLE_SCHEMAS["DatabricksMetrics_CL"]="TimeGenerated=datetime metric_name=string metric_value=real timestamp=long tags=dynamic additional_attributes=dynamic"
TABLE_SCHEMAS["DatabricksLogs_CL"]="TimeGenerated=datetime message=string status=string timestamp=long tags=dynamic additional_attributes=dynamic"
TABLE_SCHEMAS["DatabricksEvents_CL"]="TimeGenerated=datetime message=string status=string timestamp=long tags=dynamic additional_attributes=dynamic"

for TABLE_NAME in "${!TABLE_SCHEMAS[@]}"; do
    az monitor log-analytics workspace table create \
        --resource-group "$RESOURCE_GROUP" \
        --workspace-name "$WORKSPACE_NAME" \
        --name "$TABLE_NAME" \
        --columns ${TABLE_SCHEMAS[$TABLE_NAME]}
done

# Create Data Collection Rule

SUBSCRIPTION_ID=$(az account show --query "id" -o tsv)
DCE_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Insights/dataCollectionEndpoints/$DCE_NAME"
WORKSPACE_RESOURCE_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.OperationalInsights/workspaces/$WORKSPACE_NAME"

# Stream declarations
STREAM_DECLARATIONS='{
  "Custom-DatabricksMetrics_CL": {
    "columns": [
      {"name": "TimeGenerated", "type": "datetime"},
      {"name": "metric_name", "type": "string"},
      {"name": "metric_value", "type": "real"},
      {"name": "timestamp", "type": "long"},
      {"name": "tags", "type": "dynamic"},
      {"name": "additional_attributes", "type": "dynamic"}
    ]
  },
  "Custom-DatabricksLogs_CL": {
    "columns": [
      {"name": "TimeGenerated", "type": "datetime"},
      {"name": "message", "type": "string"},
      {"name": "status", "type": "string"},
      {"name": "timestamp", "type": "long"},
      {"name": "tags", "type": "dynamic"},
      {"name": "additional_attributes", "type": "dynamic"}
    ]
  },
  "Custom-DatabricksEvents_CL": {
    "columns": [
      {"name": "TimeGenerated", "type": "datetime"},
      {"name": "message", "type": "string"},
      {"name": "status", "type": "string"},
      {"name": "timestamp", "type": "long"},
      {"name": "tags", "type": "dynamic"},
      {"name": "additional_attributes", "type": "dynamic"}
    ]
  }
}'

# Data flows
DATA_FLOWS='[
  {
    "streams": ["Custom-DatabricksMetrics_CL"],
    "destinations": ["databricks-workspace"],
    "transformKql": "source",
    "outputStream": "Custom-DatabricksMetrics_CL"
  },
  {
    "streams": ["Custom-DatabricksLogs_CL"],
    "destinations": ["databricks-workspace"],
    "transformKql": "source",
    "outputStream": "Custom-DatabricksLogs_CL"
  },
  {
    "streams": ["Custom-DatabricksEvents_CL"],
    "destinations": ["databricks-workspace"],
    "transformKql": "source",
    "outputStream": "Custom-DatabricksEvents_CL"
  }
]'

# Destinations
DESTINATIONS=$(cat <<EOF
{
  "logAnalytics": [
    {
      "workspaceResourceId": "$WORKSPACE_RESOURCE_ID",
      "name": "databricks-workspace"
    }
  ]
}
EOF
)

az monitor data-collection rule create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DCR_NAME" \
    --location "$LOCATION" \
    --data-collection-endpoint-id "$DCE_ID" \
    --stream-declarations "$STREAM_DECLARATIONS" \
    --data-flows "$DATA_FLOWS" \
    --destinations "$DESTINATIONS"

DCR_IMMUTABLE_ID=$(az monitor data-collection rule show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DCR_NAME" \
    --query "immutableId" -o tsv)

echo ""
echo "========================================================================"
echo "Setup completed successfully!"
echo "========================================================================"
echo ""
echo "Azure Host Name: $HOST_NAME"
echo "Azure DCR Immutable ID: $DCR_IMMUTABLE_ID"
echo ""
