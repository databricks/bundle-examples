# Note: Azure DevOps organizations are typically created through the Azure portal
# This configuration assumes the organization already exists and focuses on project creation

resource "azuredevops_project" "project" {
  name               = var.project_name
  description        = var.project_description
  visibility         = var.project_visibility
  version_control    = "Git"
  work_item_template = "Agile"

  features = {
    "boards"       = "enabled"
    "repositories" = "enabled"
    "pipelines"    = "enabled"
    "testplans"    = "disabled"
    "artifacts"    = "enabled"
  }
}

# Use the default repository created with the project
data "azuredevops_git_repository" "default_repo" {
  project_id = azuredevops_project.project.id
  name       = var.project_name
}

# Azure DevOps Build Definition (Pipeline)
resource "azuredevops_build_definition" "pipeline" {
  project_id = azuredevops_project.project.id
  name       = var.pipeline_name
  path       = "\\"

  repository {
    repo_type   = "TfsGit"
    repo_id     = data.azuredevops_git_repository.default_repo.id
    branch_name = data.azuredevops_git_repository.default_repo.default_branch
    yml_path    = var.pipeline_yml_path
  }

  ci_trigger {
    use_yaml = true
  }

  variable_groups = [
    azuredevops_variable_group.main_variables.id
  ]

  depends_on = [
    azuredevops_variable_group.main_variables
  ]
}

# Single Variable Group (following working pattern from old pipeline)
resource "azuredevops_variable_group" "main_variables" {
  project_id   = azuredevops_project.project.id
  name         = "${var.project_name}-variables"
  description  = "Main variable group for DAB deployment"
  
  # Default environment (dev)
  variable {
    name  = "env"
    value = "dev"
  }
  
  # Default Databricks host (dev)
  variable {
    name  = "DATABRICKS_HOST"
    value = var.databricks_host_dev
  }
  
  # All environment-specific Databricks hosts for pipeline overrides
  variable {
    name  = "DATABRICKS_HOST_DEV"
    value = var.databricks_host_dev
  }
  
  variable {
    name  = "DATABRICKS_HOST_TEST"
    value = var.databricks_host_test
  }
  
  variable {
    name  = "DATABRICKS_HOST_PROD"
    value = var.databricks_host_prod
  }
  
  variable {
    name  = "SERVICE_CONNECTION_NAME"
    value = var.service_connection_name
  }
}

# Pipeline authorization for the single variable group
resource "azuredevops_pipeline_authorization" "main_variables_auth" {
  project_id  = azuredevops_project.project.id
  resource_id = azuredevops_variable_group.main_variables.id
  type        = "variablegroup"
  pipeline_id = azuredevops_build_definition.pipeline.id
}