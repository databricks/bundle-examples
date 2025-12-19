# Zerobus - File Mode

This is an (experimental) template for creating a file push pipeline with Databricks Asset Bundles. 

Install it using
```
databricks bundle init --template-dir contrib/templates/file-push https://github.com/databricks/bundle-examples
```

During initialization, you'll be prompted to configure:
- **Catalog and schema** where tables will be created
- **Table definitions** including:
  - Table names and file formats (csv, json, avro, parquet)
  - Format-specific options (CSV delimiters, JSON parsing options, etc.)
  - Schema evolution settings
  - Optional schema hints

The template configures a single table during initialization. Additional tables can be added later by editing `./src/configs/tables.json`.

After initialization, follow the generated README.md to deploy and start ingesting data.