#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <dashboard_id> <target_warehouse_name> <replacements> <access_group> <dashboard name>"
    exit 1
fi

# Assign arguments to variables
dashboard_id=$1
target_warehouse_name=$2
replacements=$3
access_group=$4
dashboard_name=$5

# Function to check the result of the last command and exit if it failed
check_result() {
    if [ $1 -ne 0 ]; then
        echo "Error: $2"
        exit 1
    fi
}

clean_up() {
    rm -rf .databricks
    rm -f dev_dashboard.json
    rm -f ./src/dashboard.json
}

# Print the received arguments
echo "Dashboard ID: $dashboard_id"
echo "Target Warehouse Name: $target_warehouse_name"
echo "Replacements: $replacements"
echo "dashboard_name: $dashboard_name"

echo "============================================"
echo "Clean up the temporary files if any"
clean_up
check_result $? "Failed to clean up the temporary files"
echo "********************************************"
echo "============================================"
echo "Running script with the provided arguments..."
echo "Get the Dev Dashboard metadata json"
databricks lakeview get $dashboard_id --output json --profile dev >> dev_dashboard.json
check_result $? "Failed to get the dashboard metadata json"
echo "********************************************"
echo "============================================"
echo "modify Query in Dashboard metadata json of catalog and schema names of target workspace"
python3 dashboard_json_query_modify.py --file_path dev_dashboard.json --replacements "$replacements" --target_file ./src/dashboard.json
check_result $? "Failed to modify the dashboard metadata json"
echo "********************************************"
echo "============================================"
echo "Validate DAB bundle dashboard to the target workspace"
databricks bundle validate --var "warehouse_name=${target_warehouse_name}" --var "access_group=${access_group}" \
--var "dashboard_name=${dashboard_name}" --profile target
check_result $? "Failed to validate the dashboard bundle"
echo "********************************************"
echo "============================================"
echo "Deploy the modified dashboard to the target workspace"
databricks bundle deploy --var "warehouse_name=${target_warehouse_name}" --var "access_group=${access_group}"  \
--var "dashboard_name=${dashboard_name}" --profile target
check_result $? "Failed to deploy the dashboard bundle"
echo "********************************************"
echo "============================================"
echo "Optional-Clean up the temporary files"
clean_up
check_result $? "Failed to clean up the temporary files"
echo "********************************************"