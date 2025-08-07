# Azure DevOps CI/CD for Databricks Asset Bundles - Deployment Guide

## Overview

This Terraform configuration creates a complete Azure DevOps CI/CD solution for deploying Databricks Asset Bundles (DABs) with:
- **Automated pipeline creation** - pipeline YAML is generated and committed automatically
- **Multi-environment support** - separate dev/test/prod environments with dynamic variable group selection
- **Managed identity authentication** - secure, password-less authentication using workload identity federation
- **Smart deployment** - only deploys changed DAB folders for efficiency

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
   service_connection_name_dev = "dev-Service-Connection"
   databricks_host_dev = "https://adb-1234567890123456.1.azuredatabricks.net/"
   
   # Test Environment
   azure_subscription_id_test = "your-test-subscription-id"
   azure_subscription_name_test = "your-test-subscription-name"
   service_connection_name_test = "test-Service-Connection"
   databricks_host_test = "https://adb-1234567890123456.1.azuredatabricks.net/"
   
   # Prod Environment
   azure_subscription_id_prod = "your-prod-subscription-id"
   azure_subscription_name_prod = "your-prod-subscription-name"
   service_connection_name_prod = "prod-Service-Connection"
   databricks_host_prod = "https://adb-1234567890123456.1.azuredatabricks.net/"
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

### 5. Post-Deployment - Pipeline Ready to Use

#### ✨ Fully Automated Pipeline Setup
The Terraform deployment automatically creates and configures everything needed for CI/CD:

1. **Auto-generated `azure-pipelines.yml`** - Pipeline configuration is created and committed to your repository
2. **Variable group authorization** - Pipeline is pre-authorized to access all variable groups  
3. **Service connection permissions** - Managed identities are configured with proper access
4. **Repository initialization** - Empty repository is initialized with the pipeline file

The pipeline is **immediately ready to use** with:

- **Conditional variable group selection** based on branch (dev/test/main)
- **Dynamic environment targeting** using the variable groups created by Terraform:
  - `{pipeline_name}-Dev-Variables` (for dev branch)
  - `{pipeline_name}-Test-Variables` (for test branch)  
  - `{pipeline_name}-Prod-Variables` (for main branch)
- **DAB change detection** to deploy only modified bundles
- **Sequential deployment** with comprehensive error handling
- **Skip logic** to avoid unnecessary deployments when no changes are detected

Each variable group contains:
- `env` - Environment name (dev/test/prod)
- `DATABRICKS_HOST` - Environment-specific Databricks workspace URL
- `SERVICE_CONNECTION_NAME` - Environment-specific service connection name

**✅ No manual pipeline configuration required** - everything works immediately after `terraform apply`!

#### Add Your DAB Projects
1. **Clone the created repository**:
   ```bash
   git clone https://dev.azure.com/{org}/{project}/_git/{project}
   cd {project}
   ```

2. **Create DAB folders anywhere in the repository**:
   ```
   your-repo/
   ├── azure-pipelines.yml        # ✨ Already created by Terraform
   ├── data-pipeline/             # Your DAB folders can be anywhere
   │   ├── databricks.yml
   │   └── src/
   ├── ml-workflows/
   │   ├── databricks.yml
   │   └── notebooks/
   └── analytics/
       ├── databricks.yml
       └── queries/
   ```
   
   The pipeline automatically detects **any folder containing `databricks.yml`** (searches up to 7 levels deep).

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
- Check that service connection names follow the pattern: `{env}-Service-Connection`
- Ensure managed identity has proper federated credential configuration
- Verify the service connection names in variable groups match the actual service connections created

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
- Verify changes include files with `databricks.yml` (DAB folders can be anywhere in repo)
- Ensure pipeline YAML path is correct in Terraform configuration
- Check branch names match trigger configuration (dev/test/main)

#### 4. Pipeline variables are empty or malformed
**Problem**: Debug output shows empty values like `Build.Reason: `, `env variable: `, or malformed `DATABRICKS_HOST: ://workspace.net`

**Solution**:
- This indicates variable group selection is not working properly
- Check that your branch names match exactly: `dev`, `test`, `main`
- Verify terraform.tfvars contains complete values (no `<your-...>` placeholders)
- Ensure service connection names follow pattern: `dev-Service-Connection`, `test-Service-Connection`, `prod-Service-Connection`
- Re-run `terraform apply` if you updated terraform.tfvars after initial deployment

#### 5. "Access denied to Azure DevOps"
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

After successful deployment:
1. **Clone your repository** and add DAB folders anywhere in the repo structure
2. **Create your first DAB** with a `databricks.yml` file
3. **Test the pipeline** by creating a branch and making changes  
4. **Set up branch policies** for production deployments (require PR reviews for main branch)
5. **Configure notifications** for pipeline results (Azure DevOps → Project Settings → Notifications)
6. **Add monitoring** for deployed DABs using Databricks system tables or Azure Monitor
7. **Scale up** by adding more DAB projects - pipeline automatically detects all `databricks.yml` files

## Summary

This fully automated solution provides:

- ✅ **Complete Automation**: Single `terraform apply` creates everything - no manual configuration needed
- 🏗️ **Enterprise Architecture**: Environment isolation with centralized CI/CD management  
- 🔐 **Zero Secrets**: Managed identity authentication - no passwords or keys to manage
- 🎯 **Smart Deployment**: Only deploys changed DAB folders for efficiency
- 🌐 **Multi-Environment**: Automatic dev/test/prod environment selection based on git branch
- 📋 **Production Ready**: Comprehensive error handling, logging, and pipeline authorization
- 🚀 **Immediate Use**: Pipeline is configured and ready to use as soon as Terraform completes

**Perfect for teams who want enterprise-grade DAB CI/CD without the complexity!**