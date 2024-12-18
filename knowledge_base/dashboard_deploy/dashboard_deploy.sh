#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <dashboard_id> <dev_workspace> <target_workspace> <target_warehouse_name> <replacements> <access_group> <dashboard name>"
    exit 1
fi

# Assign arguments to variables
dashboard_id=$1
dev_workspace=$2
target_workspace=$3
target_warehouse_name=$4
replacements=$5
access_group=$6
dashboard_name=$7

# Print the received arguments
echo "Dashboard ID: $dashboard_id"
echo "Development Workspace: $dev_workspace"
echo "Target Workspace: $target_workspace"
echo "Target Warehouse Name: $target_warehouse_name"
echo "Replacements: $replacements"
echo "dashboard_name: $dashboard_name"


echo "Running script with the provided arguments..."

rm dev_dashboard.json
echo "============================================"
echo "Get the Dev Dashboard metadata json"
databricks lakeview get $dashboard_id --output json --profile dev >> dev_dashboard.json

echo "============================================"
echo "modify Query in Dashboard metadata json of catalog and schema names of target workspace"
rm ./src/dashboard.json
python3 dashboard_json_query_modify.py --file_path dev_dashboard.json --replacements "$replacements" --target_file ./src/dashboard.json

echo "============================================"
echo "Validate DAB bundle dashboard to the target workspace"
databricks bundle validate --var "dev_workspace=$dev_workspace" --var "target_workspace=${target_workspace}" \
--var "warehouse_name=${target_warehouse_name}" --var "access_group=${access_group}" --var "dashboard_name=${dashboard_name}" --profile target

echo "============================================"
echo "Deploy the modified dashboard to the target workspace"
databricks bundle deploy --var "dev_workspace=${dev_workspace}" --var "target_workspace=${target_workspace}" \
--var "warehouse_name=${target_warehouse_name}" --var "access_group=${access_group}" --var "dashboard_name=${dashboard_name}" --profile target