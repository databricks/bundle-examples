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

# Initialize the default repository by creating a simple initial commit using local-exec
resource "null_resource" "initialize_repo" {
  provisioner "local-exec" {
    command = <<-EOT
      # Create a temporary directory for initialization
      TEMP_DIR=$(mktemp -d)
      cd "$TEMP_DIR"
      
      # Initialize git and create initial commit
      git init
      git config user.email "terraform@example.com"
      git config user.name "Terraform"
      
      # Create initial README
      echo "# ${var.project_name}" > README.md
      echo "" >> README.md
      echo "This repository contains Databricks Asset Bundles (DABs) with automated CI/CD deployment." >> README.md
      
      git add README.md
      git commit -m "Initial commit"
      
      # Add remote and push to initialize the repository
      git remote add origin "${data.azuredevops_git_repository.default_repo.remote_url}"
      git branch -M main
      git push -u origin main
      
      # Cleanup
      cd /
      rm -rf "$TEMP_DIR"
    EOT
  }

  depends_on = [azuredevops_project.project]
}

# Create the azure-pipelines.yml file after repository initialization
resource "azuredevops_git_repository_file" "azure_pipeline_yml" {
  repository_id       = data.azuredevops_git_repository.default_repo.id
  file                = var.pipeline_yml_path
  content = replace(
    replace(
      replace(
        file("${path.module}/templates/azure-pipelines.yml.tpl"),
        "PIPELINE_NAME_DEV", "${var.pipeline_name}-Dev-Variables"
      ),
      "PIPELINE_NAME_TEST", "${var.pipeline_name}-Test-Variables"
    ),
    "PIPELINE_NAME_PROD", "${var.pipeline_name}-Prod-Variables"
  )
  branch              = "refs/heads/main"
  commit_message      = "Add DAB CI/CD pipeline configuration via Terraform"
  overwrite_on_create = true
  depends_on          = [null_resource.initialize_repo]
}

