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
output "main_variable_group_name" {
  description = "Name of the main variable group"
  value       = azuredevops_variable_group.main_variables.name
}

output "main_variable_group_id" {
  description = "ID of the main variable group"
  value       = azuredevops_variable_group.main_variables.id
}