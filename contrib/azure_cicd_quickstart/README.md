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

1. **Copy the template file**:
   ```bash
   cp terraform.tfvars.template terraform.tfvars
   ```

2. **Edit terraform.tfvars** with your values:
   ```hcl
   # Azure DevOps Organization
   organization_name = "your-org-name"           # From https://dev.azure.com/{org-name}
   organization_id = "12345678-1234-1234-1234-123456789abc"  # Organization GUID
   
   # Project Configuration  
   project_name = "dab-deployment-project"
   repository_name = "dab-repository"
   pipeline_name = "DAB-CI-Pipeline"
   
   # Azure Subscription
   azure_subscription_id = "your-subscription-id"
   azure_subscription_name = "your-subscription-name"
   resource_group_name = "your-resource-group"
   
   # Service Connection
   service_connection_name = "dab-service-connection"
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

1. **Initialize Terraform**:
   ```bash
   terraform init
   ```

2. **Validate Configuration**:
   ```bash
   terraform validate
   terraform plan
   ```

3. **Deploy Resources**:
   ```bash
   terraform apply
   ```

### 5. Post-Deployment Configuration

#### Update Pipeline Variables
After deployment, update the pipeline YAML variables:

```yaml
variables:
  - name: DATABRICKS_HOST
    value: 'https://your-databricks-workspace-url'
  - name: SERVICE_CONNECTION_NAME  
    value: 'your-service-connection-name'  # Must match tfvars
```

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
   - PR should trigger validation pipeline
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
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Azure DevOps  │    │     Azure       │    │   Databricks    │
│                 │    │                 │    │                 │
│  ┌─────────────┐│    │┌─────────────────│    │                 │
│  │   Pipeline  ││    ││Managed Identity │    │   Workspace     │
│  │             ││────┤│                 │────│                 │
│  │ - PR Val.   ││    ││Federated Cred.  │    │   DAB Deploy    │
│  │ - Deploy    ││    │└─────────────────│    │                 │
│  └─────────────┘│    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Next Steps

After successful deployment:
1. Create additional DAB projects in `data_eng_bundles/`
2. Set up branch policies for production deployments
3. Configure notifications for pipeline results
4. Implement additional environments (test, prod)
5. Add monitoring and logging for deployed DABs