# User-Assigned Managed Identities for Each Environment
resource "azurerm_user_assigned_identity" "dev_pipeline_identity" {
  name                = "${var.project_name}-dev-identity"
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

resource "azurerm_user_assigned_identity" "test_pipeline_identity" {
  name                = "${var.project_name}-test-identity"
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

resource "azurerm_user_assigned_identity" "prod_pipeline_identity" {
  name                = "${var.project_name}-prod-identity"
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

# Federated Identity Credentials for Each Environment
resource "azurerm_federated_identity_credential" "dev_pipeline_federated_credential" {
  name                = "${var.project_name}-dev-federated-credential"
  resource_group_name = data.azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.dev_pipeline_identity.id
  
  audience = ["api://AzureADTokenExchange"]
  issuer   = "https://vstoken.dev.azure.com/${var.organization_id}"
  subject  = "sc://${var.organization_name}/${var.project_name}/${var.service_connection_name_dev}"

  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
  }
}

resource "azurerm_federated_identity_credential" "test_pipeline_federated_credential" {
  name                = "${var.project_name}-test-federated-credential"
  resource_group_name = data.azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.test_pipeline_identity.id
  
  audience = ["api://AzureADTokenExchange"]
  issuer   = "https://vstoken.dev.azure.com/${var.organization_id}"
  subject  = "sc://${var.organization_name}/${var.project_name}/${var.service_connection_name_test}"

  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
  }
}

resource "azurerm_federated_identity_credential" "prod_pipeline_federated_credential" {
  name                = "${var.project_name}-prod-federated-credential"
  resource_group_name = data.azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.prod_pipeline_identity.id
  
  audience = ["api://AzureADTokenExchange"]
  issuer   = "https://vstoken.dev.azure.com/${var.organization_id}"
  subject  = "sc://${var.organization_name}/${var.project_name}/${var.service_connection_name_prod}"

  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
  }
}

# Role Assignments - Reader on Each Subscription
resource "azurerm_role_assignment" "dev_pipeline_identity_reader" {
  scope                = "/subscriptions/${var.azure_subscription_id_dev}"
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.dev_pipeline_identity.principal_id

  depends_on = [azurerm_user_assigned_identity.dev_pipeline_identity]
}

resource "azurerm_role_assignment" "test_pipeline_identity_reader" {
  scope                = "/subscriptions/${var.azure_subscription_id_test}"
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.test_pipeline_identity.principal_id

  depends_on = [azurerm_user_assigned_identity.test_pipeline_identity]
}

resource "azurerm_role_assignment" "prod_pipeline_identity_reader" {
  scope                = "/subscriptions/${var.azure_subscription_id_prod}"
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.prod_pipeline_identity.principal_id

  depends_on = [azurerm_user_assigned_identity.prod_pipeline_identity]
}

# Azure DevOps Service Connections for Each Environment
resource "azuredevops_serviceendpoint_azurerm" "dev_pipeline_service_connection" {
  project_id                             = azuredevops_project.project.id
  service_endpoint_name                  = var.service_connection_name_dev
  description                           = "Service connection for ${var.project_name} dev environment using managed identity"
  service_endpoint_authentication_scheme = "WorkloadIdentityFederation"
  
  credentials {
    serviceprincipalid = azurerm_user_assigned_identity.dev_pipeline_identity.client_id
  }
  
  azurerm_spn_tenantid      = data.azurerm_client_config.current.tenant_id
  azurerm_subscription_id   = var.azure_subscription_id_dev
  azurerm_subscription_name = var.azure_subscription_name_dev

  depends_on = [
    azurerm_federated_identity_credential.dev_pipeline_federated_credential,
    azurerm_role_assignment.dev_pipeline_identity_reader
  ]
}

resource "azuredevops_serviceendpoint_azurerm" "test_pipeline_service_connection" {
  project_id                             = azuredevops_project.project.id
  service_endpoint_name                  = var.service_connection_name_test
  description                           = "Service connection for ${var.project_name} test environment using managed identity"
  service_endpoint_authentication_scheme = "WorkloadIdentityFederation"
  
  credentials {
    serviceprincipalid = azurerm_user_assigned_identity.test_pipeline_identity.client_id
  }
  
  azurerm_spn_tenantid      = data.azurerm_client_config.current.tenant_id
  azurerm_subscription_id   = var.azure_subscription_id_test
  azurerm_subscription_name = var.azure_subscription_name_test

  depends_on = [
    azurerm_federated_identity_credential.test_pipeline_federated_credential,
    azurerm_role_assignment.test_pipeline_identity_reader
  ]
}

resource "azuredevops_serviceendpoint_azurerm" "prod_pipeline_service_connection" {
  project_id                             = azuredevops_project.project.id
  service_endpoint_name                  = var.service_connection_name_prod
  description                           = "Service connection for ${var.project_name} prod environment using managed identity"
  service_endpoint_authentication_scheme = "WorkloadIdentityFederation"
  
  credentials {
    serviceprincipalid = azurerm_user_assigned_identity.prod_pipeline_identity.client_id
  }
  
  azurerm_spn_tenantid      = data.azurerm_client_config.current.tenant_id
  azurerm_subscription_id   = var.azure_subscription_id_prod
  azurerm_subscription_name = var.azure_subscription_name_prod

  depends_on = [
    azurerm_federated_identity_credential.prod_pipeline_federated_credential,
    azurerm_role_assignment.prod_pipeline_identity_reader
  ]
}

# Data source to get current Azure configuration
data "azurerm_client_config" "current" {}

# Data source to get the resource group (assuming it exists)
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}