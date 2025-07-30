variable "organization_name" {
  description = "The name of the Azure DevOps organization"
  type        = string
  
  validation {
    condition     = length(var.organization_name) > 0
    error_message = "Organization name cannot be empty."
  }
}

variable "organization_id" {
  description = "The GUID of the Azure DevOps organization (for workload identity federation)"
  type        = string
  
  validation {
    condition = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.organization_id))
    error_message = "Organization ID must be a valid GUID format (e.g., 12345678-1234-1234-1234-123456789abc)."
  }
}

variable "project_name" {
  description = "The name of the Azure DevOps project"
  type        = string
}

variable "project_description" {
  description = "The description of the Azure DevOps project"
  type        = string
  default     = ""
}

variable "project_visibility" {
  description = "The visibility of the project (private or public)"
  type        = string
  default     = "private"
}


variable "pipeline_name" {
  description = "The name of the Azure DevOps pipeline"
  type        = string
}

variable "pipeline_yml_path" {
  description = "Path to the azure-pipelines.yml file in the repository"
  type        = string
  default     = "azure-pipelines.yml"
}

# Service Connection Variables
variable "service_connection_name" {
  description = "Name for the Azure DevOps service connection"
  type        = string
  default     = "azure-databricks-connection"
}

variable "azure_subscription_id" {
  description = "Azure subscription ID where resources will be deployed"
  type        = string
  
  validation {
    condition = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.azure_subscription_id))
    error_message = "Azure subscription ID must be a valid GUID format."
  }
}

variable "azure_subscription_name" {
  description = "Azure subscription name"
  type        = string
  
  validation {
    condition     = length(var.azure_subscription_name) > 0
    error_message = "Azure subscription name cannot be empty."
  }
}

variable "environment_name" {
  description = "Environment name for federated identity (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "azdo_personal_access_token" {
  description = "Azure DevOps Personal Access Token"
  type        = string
  sensitive   = true
}

variable "resource_group_name" {
  description = "Name of the Azure Resource Group where the managed identity will be created"
  type        = string
  
  validation {
    condition     = length(var.resource_group_name) > 0
    error_message = "Resource group name cannot be empty."
  }
}

# Environment-specific Databricks workspace URLs
variable "databricks_host_dev" {
  description = "Databricks workspace URL for development environment"
  type        = string
  
  validation {
    condition     = can(regex("^https://.*\\.azuredatabricks\\.net/?$", var.databricks_host_dev))
    error_message = "Databricks host must be a valid Azure Databricks URL."
  }
}

variable "databricks_host_test" {
  description = "Databricks workspace URL for test environment"
  type        = string
  
  validation {
    condition     = can(regex("^https://.*\\.azuredatabricks\\.net/?$", var.databricks_host_test))
    error_message = "Databricks host must be a valid Azure Databricks URL."
  }
}

variable "databricks_host_prod" {
  description = "Databricks workspace URL for production environment"
  type        = string
  
  validation {
    condition     = can(regex("^https://.*\\.azuredatabricks\\.net/?$", var.databricks_host_prod))
    error_message = "Databricks host must be a valid Azure Databricks URL."
  }
}

