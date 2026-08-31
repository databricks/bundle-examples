# job_with_condition_task

Example to show how a "condition task" can be used.

## Usage

Configure the workspace to use:
```sh
export DATABRICKS_CONFIG_PROFILE="<workspace profile>"
```

Modify the SQL warehouse name in the configuration to a running SQL warehouse in your workspace.
You can list the SQL warehouses in your workspace using the following command:
```sh
databricks warehouses list
```

Deploy the bundle:
```sh
databricks bundle deploy
```

Run and observe the SQL query task is **not** executed:
```sh
databricks bundle run example_job
```

Run and observe the SQL query task is executed:
```sh
databricks bundle run example_job --params "run_sql_task=true"
```
