# User-Assigned Managed Identity for Pipeline
resource "azurerm_user_assigned_identity" "pipeline_identity" {
  name                = "${var.project_name}-pipeline-identity"
  location            = data.azurerm_resource_group.main.location
  resource_group_name = data.azurerm_resource_group.main.name

  lifecycle {
    create_before_destroy = true
  }

  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
  }
}

# Federated Identity Credential for Azure DevOps
resource "azurerm_federated_identity_credential" "pipeline_federated_credential" {
  name                = "${var.project_name}-pipeline-federated-credential"
  resource_group_name = data.azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.pipeline_identity.id
  
  audience = ["api://AzureADTokenExchange"]
  issuer   = "https://vstoken.dev.azure.com/${var.organization_id}"
  subject  = "sc://${var.organization_name}/${var.project_name}/${var.service_connection_name}"

  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
  }
}

# Role Assignment - Reader on Subscription
resource "azurerm_role_assignment" "pipeline_identity_reader" {
  scope                = "/subscriptions/${var.azure_subscription_id}"
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.pipeline_identity.principal_id

  depends_on = [azurerm_user_assigned_identity.pipeline_identity]
}

# Azure DevOps Service Connection
resource "azuredevops_serviceendpoint_azurerm" "pipeline_service_connection" {
  project_id                             = azuredevops_project.project.id
  service_endpoint_name                  = var.service_connection_name
  description                           = "Service connection for ${var.project_name} pipeline using managed identity"
  service_endpoint_authentication_scheme = "WorkloadIdentityFederation"
  
  credentials {
    serviceprincipalid = azurerm_user_assigned_identity.pipeline_identity.client_id
  }
  
  azurerm_spn_tenantid      = data.azurerm_client_config.current.tenant_id
  azurerm_subscription_id   = var.azure_subscription_id
  azurerm_subscription_name = var.azure_subscription_name

  depends_on = [
    azurerm_federated_identity_credential.pipeline_federated_credential,
    azurerm_role_assignment.pipeline_identity_reader
  ]
}

# Data source to get current Azure configuration
data "azurerm_client_config" "current" {}

# Data source to get the resource group (assuming it exists)
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}