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



