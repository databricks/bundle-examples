resource "azuredevops_build_definition" "pipeline" {
  project_id = azuredevops_project.project.id
  name       = var.pipeline_name
  path       = "\\"

  repository {
    repo_type   = "TfsGit"
    repo_id     = data.azuredevops_git_repository.default_repo.id
    branch_name = "refs/heads/main"
    yml_path    = var.pipeline_yml_path
  }

  ci_trigger {
    use_yaml = true
  }

  variable_groups = [
    azuredevops_variable_group.dev_variables.id,
    azuredevops_variable_group.test_variables.id,
    azuredevops_variable_group.prod_variables.id
  ]

  depends_on = [
    azuredevops_variable_group.dev_variables,
    azuredevops_variable_group.test_variables,
    azuredevops_variable_group.prod_variables,
    null_resource.initialize_repo,
    azuredevops_git_repository_file.azure_pipeline_yml
  ]
}


# Dev Environment Variable Group
resource "azuredevops_variable_group" "dev_variables" {
  project_id   = azuredevops_project.project.id
  name         = "${var.pipeline_name}-Dev-Variables"
  description  = "Variable group for dev environment DAB deployment"
  
  variable {
    name  = "env"
    value = "dev"
  }
  
  variable {
    name  = "DATABRICKS_HOST"
    value = var.databricks_host_dev
  }
  
  variable {
    name  = "SERVICE_CONNECTION_NAME"
    value = var.service_connection_name_dev
  }
}

# Test Environment Variable Group
resource "azuredevops_variable_group" "test_variables" {
  project_id   = azuredevops_project.project.id
  name         = "${var.pipeline_name}-Test-Variables"
  description  = "Variable group for test environment DAB deployment"
  
  variable {
    name  = "env"
    value = "test"
  }
  
  variable {
    name  = "DATABRICKS_HOST"
    value = var.databricks_host_test
  }
  
  variable {
    name  = "SERVICE_CONNECTION_NAME"
    value = var.service_connection_name_test
  }
}

# Prod Environment Variable Group
resource "azuredevops_variable_group" "prod_variables" {
  project_id   = azuredevops_project.project.id
  name         = "${var.pipeline_name}-Prod-Variables"
  description  = "Variable group for prod environment DAB deployment"
  
  variable {
    name  = "env"
    value = "prod"
  }
  
  variable {
    name  = "DATABRICKS_HOST"
    value = var.databricks_host_prod
  }
  
  variable {
    name  = "SERVICE_CONNECTION_NAME"
    value = var.service_connection_name_prod
  }
}


# Pipeline authorization for all variable groups
resource "azuredevops_pipeline_authorization" "dev_variables_auth" {
  project_id  = azuredevops_project.project.id
  resource_id = azuredevops_variable_group.dev_variables.id
  type        = "variablegroup"
  pipeline_id = azuredevops_build_definition.pipeline.id
}

resource "azuredevops_pipeline_authorization" "test_variables_auth" {
  project_id  = azuredevops_project.project.id
  resource_id = azuredevops_variable_group.test_variables.id
  type        = "variablegroup"
  pipeline_id = azuredevops_build_definition.pipeline.id
}

resource "azuredevops_pipeline_authorization" "prod_variables_auth" {
  project_id  = azuredevops_project.project.id
  resource_id = azuredevops_variable_group.prod_variables.id
  type        = "variablegroup"
  pipeline_id = azuredevops_build_definition.pipeline.id
}

# Pipeline authorization for service connections
resource "azuredevops_pipeline_authorization" "dev_service_connection_auth" {
  project_id  = azuredevops_project.project.id
  resource_id = azuredevops_serviceendpoint_azurerm.dev_pipeline_service_connection.id
  type        = "endpoint"
  pipeline_id = azuredevops_build_definition.pipeline.id
}

resource "azuredevops_pipeline_authorization" "test_service_connection_auth" {
  project_id  = azuredevops_project.project.id
  resource_id = azuredevops_serviceendpoint_azurerm.test_pipeline_service_connection.id
  type        = "endpoint"
  pipeline_id = azuredevops_build_definition.pipeline.id
}

resource "azuredevops_pipeline_authorization" "prod_service_connection_auth" {
  project_id  = azuredevops_project.project.id
  resource_id = azuredevops_serviceendpoint_azurerm.prod_pipeline_service_connection.id
  type        = "endpoint"
  pipeline_id = azuredevops_build_definition.pipeline.id
}