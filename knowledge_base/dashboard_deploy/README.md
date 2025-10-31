# Dashboard Deployment to higher environment

This example demonstrates how to deploy the existing dashboard from dev to target Databricks workspace, using dab bundle
it also allows you to change the catalog and schema names of dashboard json dataset query from dev to target
specifies access to the groups on the target dashboard

For more information about AI/BI dashboards, please refer to the [documentation](https://docs.databricks.com/dashboards/index.html).

## Prerequisites

* Databricks CLI v0.232.0 or above
* Databricks configuration file (`~/.databricks.cfg`) with a profile named dev and target workspace configured
* The catalog, schema and tables mentioned in dashboard datasets exists in target workspace


## Usage

Invoke the shell script dashboard_deploy.sh to deploy the dashboard from dev to target Databricks workspace.

Example
``` sh
 #                     'dev-dashboard-id'              'target-warehouse  'dev to target catalog/schema mapping'           'access   'target dashboard name'
 #                                                       name'                                                               group' 
                        
sh dashboard_deploy.sh 01efbbade84416dc984927ca794fd768 'Shared Endpoint' '{"samples": "shared", "nyctaxi": "ru_nyctaxi"}' test_group client_dashboard
```
Output

Clean up the temporary files if any
********************************************
============================================
Running script with the provided arguments...
Get the Dev Dashboard metadata json
********************************************
============================================
modify Query in Dashboard metadata json of catalog and schema names of target workspace
Namespace(file_path='dev_dashboard.json', replacements='{"samples": "shared", "nyctaxi": "ru_nyctaxi"}', target_file='./src/dashboard.json')
{"samples": "shared", "nyctaxi": "ru_nyctaxi"}
********************************************
============================================
Validate DAB bundle dashboard to the target workspace
Name: client_dashboard
Target: target
Workspace:
User: rushabh.mehta@databricks.com
Path: /Workspace/Users/rushabh.mehta@databricks.com/.bundle/client_dashboard/target

Validation OK!
********************************************
============================================
Deploy the modified dashboard to the target workspace
Uploading bundle files to /Workspace/Users/rushabh.mehta@databricks.com/.bundle/client_dashboard/target/files...
Deploying resources...
Updating deployment state...
Deployment complete!
********************************************
============================================
Optional-Clean up the temporary files

