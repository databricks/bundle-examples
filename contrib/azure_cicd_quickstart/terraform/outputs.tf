output "project_id" {
  description = "The ID of the created project"
  value       = azuredevops_project.project.id
}

output "repository_id" {
  description = "The ID of the default repository"
  value       = data.azuredevops_git_repository.default_repo.id
}

output "repository_clone_url" {
  description = "The clone URL of the repository"
  value       = data.azuredevops_git_repository.default_repo.remote_url
}

output "pipeline_id" {
  description = "The ID of the created pipeline"
  value       = azuredevops_build_definition.pipeline.id
}

output "pipeline_url" {
  description = "The URL of the pipeline"
  value       = "https://dev.azure.com/${var.organization_name}/${azuredevops_project.project.name}/_build?definitionId=${azuredevops_build_definition.pipeline.id}"
}

# Variable Group Outputs
output "dev_variable_group_name" {
  description = "Name of the dev variable group"
  value       = azuredevops_variable_group.dev_variables.name
}

output "test_variable_group_name" {
  description = "Name of the test variable group"
  value       = azuredevops_variable_group.test_variables.name
}

output "prod_variable_group_name" {
  description = "Name of the prod variable group"
  value       = azuredevops_variable_group.prod_variables.name
}

# Service Connection Outputs
output "dev_service_connection_name" {
  description = "Name of the dev service connection"
  value       = azuredevops_serviceendpoint_azurerm.dev_pipeline_service_connection.service_endpoint_name
}

output "test_service_connection_name" {
  description = "Name of the test service connection"
  value       = azuredevops_serviceendpoint_azurerm.test_pipeline_service_connection.service_endpoint_name
}

output "prod_service_connection_name" {
  description = "Name of the prod service connection"
  value       = azuredevops_serviceendpoint_azurerm.prod_pipeline_service_connection.service_endpoint_name
}

# Managed Identity Outputs
output "dev_managed_identity_name" {
  description = "Name of the dev managed identity"
  value       = azurerm_user_assigned_identity.dev_pipeline_identity.name
}

output "test_managed_identity_name" {
  description = "Name of the test managed identity"
  value       = azurerm_user_assigned_identity.test_pipeline_identity.name
}

output "prod_managed_identity_name" {
  description = "Name of the prod managed identity"
  value       = azurerm_user_assigned_identity.prod_pipeline_identity.name
}

# Repository Files Output
output "readme_file" {
  description = "README file created in repository"
  value       = "README.md"
}

output "pipeline_file_path" {
  description = "Path to the auto-created pipeline YAML file"
  value       = var.pipeline_yml_path
}

# Summary Output
output "deployment_summary" {
  description = "Summary of all created resources"
  value = {
    project_name = var.project_name
    pipeline_name = var.pipeline_name
    pipeline_file = var.pipeline_yml_path
    variable_groups = {
      dev  = azuredevops_variable_group.dev_variables.name
      test = azuredevops_variable_group.test_variables.name
      prod = azuredevops_variable_group.prod_variables.name
    }
    service_connections = {
      dev  = azuredevops_serviceendpoint_azurerm.dev_pipeline_service_connection.service_endpoint_name
      test = azuredevops_serviceendpoint_azurerm.test_pipeline_service_connection.service_endpoint_name
      prod = azuredevops_serviceendpoint_azurerm.prod_pipeline_service_connection.service_endpoint_name
    }
    managed_identities = {
      dev  = azurerm_user_assigned_identity.dev_pipeline_identity.name
      test = azurerm_user_assigned_identity.test_pipeline_identity.name
      prod = azurerm_user_assigned_identity.prod_pipeline_identity.name
    }
  }
}