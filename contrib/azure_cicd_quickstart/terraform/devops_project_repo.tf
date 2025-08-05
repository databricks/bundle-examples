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
# Note: If you have an existing Azure DevOps project, comment out the above azuredevops_project resource and use this data source to reference your project. 
# data "azuredevops_project" "project" {
#   name = "Example Project"
# }

# Use the default repository created with the project
data "azuredevops_git_repository" "default_repo" {
  project_id = azuredevops_project.project.id
  name       = var.project_name
}