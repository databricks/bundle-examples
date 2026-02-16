# Getting started

1. Configure the monitoring ETL

Refer to [../COMMON_CONFIGURATION.md](COMMON_CONFIGURATION.md) for common configuration options.

Additionally, for this DAB, you need to include the following as part of your deployment target configuration:

```
main_dashboard_template_path: ../../cdc_connector_monitoring_dab/dashboards/CDC Connector Monitoring Dashboard Template.lvdash.json
```

The above will include the standard AI/BI dashboard as part of the deployment. If you have created your custom dashboard, you can replace the path to it in the above option.

2. Deploy the DAB
3. Generate monitoring tables - recommended to do that manually the first time:
   1. Run the `Import CDC Connector event logs` job if you have configured  `imported_pipeline_ids` variable
   2. Run the `Scheduled runner for Monitoring ETL ... ` job
4. On successful Step 3, run the `Post-deploy actions ...` job. This will create a sample monitoring Dashboard and also annotate the monitoring tables with column comments for easier use and exploration.

# Architecture

```
                    |--------------|
                    | Import event |
                 |->| logs Job     |--|
                 |  |--------------|  |
|-------------|  |                    |
| Pipeline    |  |                    |    -------------
| without     |  |                    |-->( Imported    )--|
| Delta event |  |                    |   ( Events      )  |                        |-----------------|
| log         |--|                    |   ( Delta Tables)  |                    |-->| 3P Observability|
|-------------|  |                    |    -------------   |                    |   | Platforms sinks |
                 |  |--------------|  |                    |   |-------------|  |   |-----------------|
                 |  | Import Event |--|                    |-->| Monitoring  |--|
                 |->| logs Job     |                       |   | ETL Pipeline|  |   |------------|   |-----------|
                    |--------------|                       |   |-------------|  |-->| Monitoring |-->| Example   |
                                                           |                        | tables     |   | AI/BI     |
-------------------                      --------------    |                        |------------|   | Dashboard |
| Pipelines with  |-------------------> ( Event Log    )---|                                         |-----------|
| Delta event log |                     ( Delta Tables )
------------------                       --------------
```

# Monitoring tables

See the table and column comments in the target `monitoring_catalog`.`monitoring_schema`. Remember to run the `Post-deploy actions ...` job that populates those comments.

