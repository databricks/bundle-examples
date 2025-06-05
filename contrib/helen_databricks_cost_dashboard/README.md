# helen databricks cost dashboard

## Outline

## 📦 What’s Included

This asset bundle includes:
- A native Databricks dashboard (`.lvdash.json`) defined in `dashboards/`
- Supporting SQL queries and configuration
- A `databricks.yml` bundle configuration file for deployment
- A `Makefile` for generating and syncing dashboard assets

## 📁 Structure

```

.
├── dashboards/
│   └── Helen Databricks Cost Dashboard.lvdash.json
├── .databricks/
│   └── bundle\_config.yml             # Optional extra config
├── databricks.yml                    # Main bundle configuration
├── Makefile                          # Targets for init and sync
└── README.md                         # This file

````

## ⚙️ Requirements

- Databricks CLI v0.205.0 or later
- Asset Bundles feature enabled in the workspace
- Logged in via `databricks auth login`
- Access to target workspace and user folder

## 🚀 Usage

### Generate the Dashboard

Use the following command to generate the dashboard from an existing JSON definition:

```bash
make init
````

This runs:

```bash
databricks bundle generate dashboard \
  --existing-path '/Workspace/Users/neelabh.kashyap@helen.fi/Helen Databricks Cost Dashboard.lvdash.json'
```

### Sync to Workspace

Push changes from the local bundle to your Databricks workspace:

```bash
make sync
```

This runs:

```bash
databricks bundle deploy
```

### Preview Locally

You can preview what will be deployed:

```bash
databricks bundle validate
databricks bundle plan
```

## 📊 Dashboard Features

* Cost by subscription and environment
* Breakdown by SQL warehouse type (Serverless, Pro, Classic)
* Trends over time and forecasting
* Attribution by business unit or application
* Integration with Azure export pipelines

## 🛠 Development Notes

* Edit the `.lvdash.json` file directly to modify the dashboard.
* Use `make sync` to push updates after changes.
* Avoid manual edits in the workspace to prevent drift.
