# Azure DevOps CI/CD for Databricks Asset Bundles (DABs)

A complete solution for deploying Databricks Asset Bundles using Azure DevOps pipelines with managed identity authentication and multi-environment support.

## 🚀 Quick Start

This solution automatically creates everything you need for DAB CI/CD in Azure DevOps:

- ✅ **Azure DevOps project and pipeline**
- ✅ **Multi-environment variable groups** (dev/test/prod)  
- ✅ **Managed identities** with federated credentials
- ✅ **Service connections** for each environment
- ✅ **Automated pipeline configuration** - no manual setup required

### Prerequisites

- Azure CLI (logged in)
- Terraform >= 1.0
- Azure DevOps organization access
- Owner/Contributor permissions on target Azure subscriptions

### Setup

1. **Configure your environment**:
   ```bash
   cd terraform/
   cp terraform.tfvars.template terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Deploy infrastructure**:
   ```bash
   terraform init
   terraform apply
   ```

3. **Add Manged Identity to Databricks Workspace**:
   - View the Manged Identities in the terraform outputs
   - Add the Managed Identities into their respective workspaces

4. **Start using the pipeline**:
   - Pipeline is automatically created and configured
   - Add your DAB folders anywhere in the repository
   - Create PRs to trigger validation  
   - Merge to main/test/dev to deploy

## 📋 What Gets Created

| Component | Description |
|-----------|-------------|
| **Azure DevOps Project** | Single project containing pipeline and repository |
| **Dynamic Pipeline** | Automatically detects changed DABs and deploys only what's needed |
| **Variable Groups** | Environment-specific configuration (dev/test/prod) |
| **Managed Identities** | Secure, password-less authentication for each environment |
| **Service Connections** | Azure subscription connections using workload identity |


The pipeline automatically:
1. **Detects changed DAB folders** using git diff
2. **Selects environment** based on branch (dev/test/main)
3. **Authenticates** using managed identity
4. **Deploys only changed bundles** for efficiency
5. **Provides detailed logging** and error handling

## 📁 Repository Structure

After deployment, your repository will look like:

```
your-repo/
├── azure-pipelines.yml          # ✨ Auto-generated pipeline
├── my-data-pipeline/            # Your DAB folders
│   ├── databricks.yml          # (anywhere in repo)
│   └── src/
├── another-bundle/
│   ├── databricks.yml
│   └── notebooks/
└── terraform/                  # Infrastructure code
    └── README.md               # Detailed setup guide
```

## 🎯 Branch-Based Deployments

| Branch | Environment | Variable Group | Databricks Workspace |
|--------|------------|----------------|----------------------|
| `dev` | Development | `{pipeline_name}-Dev-Variables` | Dev workspace |
| `test` | Testing | `{pipeline_name}-Test-Variables` | Test workspace |
| `main` | Production | `{pipeline_name}-Prod-Variables` | Prod workspace |

## 📖 Detailed Documentation

For complete setup instructions, troubleshooting, and advanced configuration:

👉 **[See Terraform README](terraform/README.md)** for detailed deployment guide

## 🔧 Troubleshooting

### Common Issues

- **"No matching federated identity found"** → Check organization GUID in terraform.tfvars
- **"Resource group not found"** → Ensure resource group exists before running terraform
- **"Pipeline not triggering"** → Verify DAB folders have `databricks.yml` files

### Getting Help

1. Check the [detailed troubleshooting guide](terraform/README.md#troubleshooting)
2. Verify all prerequisite permissions are in place
3. Review Azure DevOps pipeline logs for specific error messages

## 🏗️ Architecture

This solution follows enterprise DevOps patterns:

- **Single DevOps Project**: Centralized pipeline management
- **Environment Isolation**: Separate subscriptions/workspaces per environment  
- **Managed Identity**: Secure, password-less authentication
- **Conditional Deployment**: Only changed DABs are deployed
- **Branch Protection**: Production deployments only from main branch

## 🚦 Next Steps

After successful deployment:

1. **Test the pipeline** - Create a test DAB and commit changes
2. **Set up branch policies** - Protect main branch, require PR reviews
3. **Add your DABs** - Place Databricks Asset Bundles anywhere in the repo
4. **Monitor deployments** - Use Azure DevOps pipeline history and logs
5. **Scale up** - Add more environments or customize the pipeline