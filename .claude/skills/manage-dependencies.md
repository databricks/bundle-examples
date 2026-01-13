---
name: manage-dependencies
description: Expert assistance with artifacts, wheels, libraries, and dependencies. Use when users need help building Python packages, configuring library dependencies, or managing private packages.
---

# Artifacts & Dependencies - Package Management Expert

## Instructions

1. **Understand packaging needs**
   - Python wheels?
   - JAR files?
   - Multiple libraries?
   - Private repositories?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/library-dependencies
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/artifact-private

3. **Find examples**
   - default_python/ - Standard wheel build
   - knowledge_base/job_with_multiple_wheels/ - Multiple packages
   - knowledge_base/private_wheel_packages/ - Private repos
   - knowledge_base/python_wheel_poetry/ - Poetry setup
   - knowledge_base/spark_jar_task/ - JAR artifacts

4. **Provide configuration**
   - artifacts section
   - pyproject.toml setup
   - Library references in tasks

## Key Patterns

### Standard Python Wheel
```yaml
bundle:
  name: my_project

artifacts:
  python_artifact:
    type: whl
    build: uv build --wheel

include:
  - resources/*.yml
```

### pyproject.toml Setup
```toml
[project]
name = "my_project"
version = "0.1.0"
dependencies = [
    "databricks-sdk>=0.1.0,<1.0.0",
    "pandas>=2.0.0,<3.0.0",
]

[dependency-groups]
dev = [
    "pytest>=7.0",
    "databricks-connect>=15.4,<15.5",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Job Using Wheel
```yaml
resources:
  jobs:
    my_job:
      name: "ETL Job"
      tasks:
        - task_key: process
          python_wheel_task:
            package_name: my_project
            entry_point: main
          libraries:
            - whl: ./dist/*.whl
```

### Multiple Wheels
```yaml
resources:
  jobs:
    multi_lib_job:
      name: "Job with Multiple Libraries"
      tasks:
        - task_key: process
          python_wheel_task:
            package_name: my_project
            entry_point: main
          libraries:
            - whl: ./dist/my_project-*.whl
            - whl: ./dist/shared_lib-*.whl
            - pypi:
                package: "requests>=2.28.0"
```

### Private Wheel Packages
```yaml
artifacts:
  my_private_wheel:
    type: whl
    build: uv build --wheel
    path: ./private_package

# In task
libraries:
  - whl: ./dist/private_package-*.whl
  - whl: https://private-repo.com/packages/library.whl
```

### Poetry Build
```yaml
artifacts:
  poetry_artifact:
    type: whl
    build: poetry build

# poetry.toml
[tool.poetry]
name = "my-project"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.10"
databricks-sdk = "^0.1.0"
```

### Spark JAR Artifact
```yaml
artifacts:
  spark_jar:
    type: jar
    build: mvn clean package

resources:
  jobs:
    scala_job:
      name: "Scala Spark Job"
      tasks:
        - task_key: process
          spark_jar_task:
            main_class_name: com.company.Main
          libraries:
            - jar: ./target/my-app.jar
```

### Environment Dependencies
```yaml
resources:
  jobs:
    env_job:
      name: "Job with Environment"
      environments:
        - environment_key: default
          spec:
            client: "1"
            dependencies:
              - "pandas==2.0.0"
              - "numpy==1.24.0"
      tasks:
        - task_key: analyze
          environment_key: default
          python_wheel_task:
            package_name: my_project
            entry_point: analyze
          libraries:
            - whl: ./dist/*.whl
```

## Build Tools

### uv (Recommended)
```yaml
artifacts:
  python_artifact:
    type: whl
    build: uv build --wheel
```

**Benefits:**
- Fast (10-100x faster than pip)
- Reliable dependency resolution
- Modern Python packaging
- Built-in virtual environment management

### Poetry
```yaml
artifacts:
  python_artifact:
    type: whl
    build: poetry build
```

**Benefits:**
- Mature dependency management
- Lock files for reproducibility
- Good for existing Poetry projects

## Dependency Best Practices

1. **Pin major versions**
   ```toml
   dependencies = [
       "databricks-sdk>=0.1.0,<1.0.0",  # Good
       "pandas>=2.0.0,<3.0.0",           # Good
       # Not: "pandas"  # Bad - unpinned
   ]
   ```

2. **Separate dev dependencies**
   ```toml
   [dependency-groups]
   dev = [
       "pytest",
       "black",
       "mypy",
   ]
   ```

3. **Test builds locally**
   ```bash
   uv build --wheel
   ls dist/  # Verify wheel created
   ```

4. **Use uv for speed**
   - Faster builds
   - Better dependency resolution
   - Simpler configuration

5. **Keep dependencies minimal**
   - Only include what you need
   - Smaller packages = faster deployment

## Library Types

### Wheel (Python)
```yaml
libraries:
  - whl: ./dist/*.whl
  - whl: /Volumes/catalog/schema/volume/package.whl
```

### PyPI Package
```yaml
libraries:
  - pypi:
      package: "pandas>=2.0.0"
```

### JAR (Java/Scala)
```yaml
libraries:
  - jar: ./target/my-app.jar
```

### Maven
```yaml
libraries:
  - maven:
      coordinates: "com.company:artifact:1.0.0"
```

## Common Issues

- **Build fails**: Check pyproject.toml syntax, run build locally
- **Package not found**: Verify artifact paths, check dist/ directory
- **Dependency conflicts**: Pin versions explicitly, test locally
- **Import errors**: Ensure package_name matches setup, check entry_point
- **Private repo access**: Configure credentials, verify network access

## Examples

```
User: "Set up Python project with wheel building"

Steps:
1. Read default_python/ example
2. Create pyproject.toml with dependencies
3. Add artifacts section with uv build
4. Show job configuration with python_wheel_task
5. Explain build → dist/*.whl → deploy flow
```

```
User: "Job needs multiple Python packages"

Steps:
1. Read knowledge_base/job_with_multiple_wheels/
2. Show libraries section with multiple whl entries
3. Explain how to build multiple packages
4. Configure artifacts for each package
```
