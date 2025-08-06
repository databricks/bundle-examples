# DAB Pipeline Deployment Guide for Customers

## Overview

This Terraform configuration creates an Azure DevOps project with a CI/CD pipeline for deploying Databricks Asset Bundles (DABs) using managed identity authentication.

## Prerequisites

### Required Tools
- **Terraform** (>= 1.0)
- **Azure CLI** (logged in with appropriate permissions)
- **Access to Azure DevOps** organization with admin permissions

### Required Permissions
- **Azure Subscription**: Owner or Contributor role
- **Azure DevOps**: Project Collection Administrator or Organization Owner
- **Azure Active Directory**: Ability to create managed identities and federated credentials

## Step-by-Step Deployment

### 1. Prepare Configuration Files

This Terraform configuration creates all resources for all environments in a **single deployment**. It will create:
- One Azure DevOps project and pipeline
- Three variable groups (Dev, Test, Prod)
- Three managed identities (one per environment)
- Three service connections (one per subscription)

1. **Copy the template file**:
   ```bash
   cp terraform.tfvars.template terraform.tfvars
   ```

2. **Edit terraform.tfvars** with your values:
   ```hcl
   # Azure DevOps Organization
   organization_name = "your-org-name"
   organization_id = "12345678-1234-1234-1234-123456789abc"
   azdo_personal_access_token = "your-azdo-pat-token"
   
   # Project Configuration
   project_name = "dab-deployment-project"
   pipeline_name = "DAB-CI-Pipeline"
   
   # Management Resource Group (where identities will be created)
   resource_group_name = "your-management-resource-group"
   
   # Dev Environment
   azure_subscription_id_dev = "your-dev-subscription-id"
   azure_subscription_name_dev = "your-dev-subscription-name"
   service_connection_name_dev = "MyProject-Dev-Connection"
   databricks_host_dev = "https://your-dev-workspace.azuredatabricks.net/"
   
   # Test Environment
   azure_subscription_id_test = "your-test-subscription-id"
   azure_subscription_name_test = "your-test-subscription-name"
   service_connection_name_test = "MyProject-Test-Connection"
   databricks_host_test = "https://your-test-workspace.azuredatabricks.net/"
   
   # Prod Environment
   azure_subscription_id_prod = "your-prod-subscription-id"
   azure_subscription_name_prod = "your-prod-subscription-name"
   service_connection_name_prod = "MyProject-Prod-Connection"
   databricks_host_prod = "https://your-prod-workspace.azuredatabricks.net/"
   ```

### 2. Get Required Values

#### Azure DevOps Organization GUID
The organization GUID is required for workload identity federation. Get it from:

**Method 1: From URL Structure**
- Go to Azure DevOps organization settings
- Look in browser developer tools for API calls containing the org GUID

**Method 2: From Error Messages** 
- Try to access a non-existent resource in your organization
- The error URL will contain your organization GUID

**Method 3: PowerShell/CLI**
```powershell
# Using Azure DevOps CLI
az devops project list --org https://dev.azure.com/{org-name}
```

#### Azure DevOps Personal Access Token (PAT)
1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Create new token with permissions:
   - **Project and Team**: Read & Write
   - **Service Connections**: Read & Write  
   - **Build**: Read & Execute
3. Copy the token value

### 3. Validate Prerequisites

1. **Azure CLI Login**:
   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```

2. **Verify Resource Group Exists**:
   ```bash
   az group show --name "your-resource-group"
   ```

3. **Test Azure DevOps Access**:
   ```bash
   # Verify you can access the organization
   curl -u :YOUR_PAT_TOKEN https://dev.azure.com/your-org/_apis/projects
   ```

### 4. Deploy Infrastructure

**Single deployment** creates all resources for all environments.

1. **Set Azure CLI to management subscription** (where resource group exists):
   ```bash
   az account set --subscription "your-management-subscription-id"
   az account show  # Verify you're in the correct subscription
   ```

2. **Initialize and Deploy**:
   ```bash
   terraform init
   terraform validate
   terraform plan
   terraform apply
   ```

**Note**: The managed identities will be created in your management subscription but will have permissions to deploy to their respective target subscriptions (dev/test/prod).

### 5. Post-Deployment Configuration

#### Pipeline YAML Configuration
After deployment, your pipeline YAML should use conditional variable group selection based on the branch. The Terraform deployment has created three variable groups:

- `{pipeline_name}-Dev-Variables` (for dev branch)
- `{pipeline_name}-Test-Variables` (for test branch)  
- `{pipeline_name}-Prod-Variables` (for main branch)

**Your pipeline should be configured like this**:
```yaml
trigger:
  branches:
    include:
      - dev
      - test
      - main

variables:
  # Dynamically select variable group based on branch
  - ${{ if eq(variables['Build.SourceBranchName'], 'dev') }}:
      - group: '{pipeline_name}-Dev-Variables'
  - ${{ elseif eq(variables['Build.SourceBranchName'], 'test') }}:
      - group: '{pipeline_name}-Test-Variables'
  - ${{ elseif eq(variables['Build.SourceBranchName'], 'main') }}:
      - group: '{pipeline_name}-Prod-Variables'

stages:
  - stage: Build
    jobs:
      - job: BuildJob
        steps:
          - script: |
              echo "Environment: $(env)"
              echo "Databricks Host: $(DATABRICKS_HOST)"
              echo "Service Connection: $(SERVICE_CONNECTION_NAME)"
```

Each variable group contains:
- `env` - Environment name (dev/test/prod)
- `DATABRICKS_HOST` - Environment-specific Databricks workspace URL
- `SERVICE_CONNECTION_NAME` - Environment-specific service connection name

#### Create DAB Folders
1. Clone the created repository
2. Create folder structure:
   ```
   data_eng_bundles/
   ├── your-dab-folder/
   │   ├── databricks.yml
   │   └── src/
   ```

### 6. Test the Pipeline

1. **Create a test DAB**:
   ```yaml
   # data_eng_bundles/test-dab/databricks.yml
   bundle:
     name: test-dab
   
   targets:
     dev:
       workspace:
         host: https://your-databricks-workspace
   ```

2. **Create a feature branch and PR**:
   ```bash
   git checkout -b test-feature
   # Make changes to your DAB
   git add .
   git commit -m "Test DAB changes"
   git push origin test-feature
   # Create PR in Azure DevOps
   ```

3. **Verify**:
   - PR should trigger change detection (no deployment)
   - Merge to main should trigger deployment pipeline

## Troubleshooting

### Common Issues

#### 1. "No matching federated identity record found"
**Problem**: Authentication error with managed identity

**Solution**:
- Verify `organization_id` in tfvars matches your actual Azure DevOps org GUID
- Check that service connection name matches between Terraform and pipeline YAML
- Ensure managed identity has proper federated credential configuration

#### 2. "Resource group not found"
**Problem**: Terraform can't find the specified resource group

**Solution**:
- Verify resource group exists: `az group show --name "your-resource-group"`
- Check Azure CLI is logged into correct subscription
- Ensure you have permissions to the resource group

#### 3. "Pipeline not triggering"
**Problem**: PR or push doesn't trigger pipeline

**Solution**:
- Check pipeline trigger settings in Azure DevOps
- Verify changes are in `data_eng_bundles/` folder
- Ensure pipeline YAML path is correct in Terraform configuration

#### 4. "Access denied to Azure DevOps"
**Problem**: PAT token doesn't have sufficient permissions

**Solution**:
- Regenerate PAT with required scopes:
  - Project and Team (Read & Write)
  - Service Connections (Read & Write)
  - Build (Read & Execute)

### Validation Commands

```bash
# Test Azure authentication
az account show

# Test Terraform configuration
terraform validate
terraform plan -var-file="terraform.tfvars"

# Test Azure DevOps access
az devops project list --org https://dev.azure.com/{org-name}

# Verify managed identity
az identity show --name "{project-name}-pipeline-identity" --resource-group "{resource-group}"
```

## Security Best Practices

1. **PAT Token Management**:
   - Use minimum required permissions
   - Set appropriate expiration dates
   - Store securely (consider Azure Key Vault)

2. **Resource Group Security**:
   - Use dedicated resource group for DAB resources
   - Apply appropriate RBAC permissions
   - Enable resource group locks if needed

3. **Service Connection**:
   - Limit service connection scope to specific subscriptions/resource groups
   - Regularly rotate credentials
   - Monitor usage and access

## Support

For issues related to:
- **Terraform Configuration**: Check variable validation messages
- **Azure DevOps**: Verify PAT permissions and organization access  
- **Azure Resources**: Ensure proper RBAC and resource group permissions
- **Databricks Integration**: Verify workspace configuration and authentication

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Azure DevOps (Single Org)                        │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │   Project       │    │  Variable Groups │    │    Pipeline     │          │
│  │  - Repository   │    │                 │    │                 │          │
│  │  - Pipeline     │    │ MyProject-Dev   │    │ Conditional     │          │
│  │                 │    │ MyProject-Test  │    │ Variable Group  │          │
│  │                 │    │ MyProject-Prod  │    │ Selection       │          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
              │                        │                        │
              │                        │                        │
┌─────────────▼─────────────┐ ┌────────▼────────┐ ┌─────────────▼─────────────┐
│     Dev Subscription      │ │ Test Subscription│ │    Prod Subscription     │
│                           │ │                 │ │                          │
│ ┌─────────────────────────┐ │ ┌───────────────┐ │ ┌─────────────────────────┐│
│ │ MyProject-dev-identity  │ │ │MyProject-test │ │ │ MyProject-prod-identity ││
│ │ + Service Connection    │ │ │+ Service Conn │ │ │ + Service Connection    ││
│ │ + Federated Credential  │ │ │+ Fed Cred     │ │ │ + Federated Credential  ││
│ └─────────────────────────┘ │ └───────────────┘ │ └─────────────────────────┘│
│                           │ │                 │ │                          │
│ ┌─────────────────────────┐ │ ┌───────────────┐ │ ┌─────────────────────────┐│
│ │   Databricks Dev        │ │ │Databricks Test│ │ │   Databricks Prod       ││
│ │   Workspace             │ │ │Workspace      │ │ │   Workspace             ││
│ └─────────────────────────┘ │ └───────────────┘ │ └─────────────────────────┘│
└───────────────────────────┘ └─────────────────┘ └───────────────────────────┘
```

## Next Steps

After successful deployment of all three environments:
1. Update your pipeline YAML to use conditional variable group selection
2. Create additional DAB projects in `data_eng_bundles/`
3. Set up branch policies for production deployments (main branch)
4. Configure notifications for pipeline results
5. Test the pipeline by creating branches and PRs for each environment
6. Add monitoring and logging for deployed DABs

## Summary

This architecture provides:
- **Environment Isolation**: Each environment has its own Azure subscription and managed identity
- **Single DevOps Project**: All environments share the same Azure DevOps project and pipeline
- **Single Deployment**: One terraform apply creates all resources for all environments
- **Dynamic Configuration**: Pipeline automatically selects the correct variable group based on branch
- **Security**: Each environment uses its own managed identity with minimal required permissions
- **Enterprise Standard**: Follows typical enterprise DevOps patterns with centralized CI/CD