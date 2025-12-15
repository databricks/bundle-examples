# bundle_variables

Example to show how bundle variables work.

We will focus on the behavior of the variables section alone. To do so, we exclusively use
the `validate` command, and use its JSON output mode to focus on the variables section.

## Usage

Configure the workspace to use:
```sh
export DATABRICKS_CONFIG_PROFILE="<workspace profile>"
```

Try to run validate without arguments:
```sh
databricks bundle validate --output json | jq .variables
```

Because the configuration includes a variable definition without a value, it returns an error
saying that the value must be defined:
```
Error: no value assigned to required variable "no_default".
```

Assign a value for this variable by either:

1. Adding a `--var` flag to all bundle commands:
```sh
databricks bundle validate --var no_default="injected value"
```

2. Configuring an environment variable:
```sh
export BUNDLE_VAR_no_default="injected value"
```

Now, try to run validate again, and observe that it passes:
```sh
databricks bundle validate --var no_default="injected value" --output json | jq .variables
```

Example output:
```json
{
  "no_default": {
    "description": "This is a variable with no default value",
    "value": "injected value"
  },
  "with_default": {
    "description": "This is a variable with a default value",
    "value": "hello"
  },
  "with_default_in_targets": {
    "default": "value_in_development",
    "description": "This is a variable with its default value defined in the targets section",
    "value": "value_in_development"
  }
}
```

What we've seen:
* The `no_default` variable is defined with the value we injected.
* The `with_default` variable is defined with the default value.
* The `with_default_in_targets` variable is defined with the value from the targets section.
