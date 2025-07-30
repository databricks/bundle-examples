terraform {
  required_providers {
    azuredevops = {
      source  = "microsoft/azuredevops"
      version = ">= 0.1.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = ">= 2.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0"
    }
  }
}

provider "azuredevops" {
  # Authentication via environment variables:
  # AZDO_PERSONAL_ACCESS_TOKEN
  # AZDO_ORG_SERVICE_URL
  org_service_url       = "https://dev.azure.com/${var.organization_name}"
  personal_access_token = var.azdo_personal_access_token
}

provider "azuread" {
  # Authentication via Azure CLI user context
  # Uses current user's az login credentials
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}
