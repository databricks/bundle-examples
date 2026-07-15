# AI Runtime training

A template for creating a bundle that launches a distributed training run on
Databricks Serverless GPU using an `ai_runtime_task`. It scaffolds the same simple
structure as the [`air_runtime_training`](../../../knowledge_base/air_runtime_training)
knowledge base example.

Install it using

```
databricks bundle init --template-dir contrib/templates/air-training https://github.com/databricks/bundle-examples
```

and follow the generated README.md to get started.

## Prompts

* `project_name` — the bundle/project name (default `air_training`).
* `accelerator_type` — the GPU SKU: `GPU_1xA10`, `GPU_1xH100`, or `GPU_8xH100`.
