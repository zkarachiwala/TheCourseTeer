# Azure Deployment Configuration Notes

## Pre-requisites
Before the GitHub Actions deployment will succeed, you must:
1.  **Create the Azure Static Web App:** This can be done via the Azure Portal or Azure CLI. Place it in the `TheCourseteerDev` resource group.
2.  **Get the Deployment Token:** Follow the instructions in the GitHub Secrets section below.
3.  **Configure GitHub Secrets:** Add the token and the database URL to your repository's secrets.

## GitHub Secrets
The following secrets must be configured in the GitHub repository (Settings > Secrets and variables > Actions):

| Secret Name | Description |
|-------------|-------------|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | The deployment token for the Azure Static Web App. **Where to find:** In the Azure Portal, navigate to your Static Web App resource -> Overview -> Select "Manage deployment token". |
| `DATABASE_URL` | The Supabase connection string (transaction pooler). |

## Azure Static Web App Environment Variables
Configure these in the Azure Portal (Static Web App > Configuration):

| Variable Name | Value |
|---------------|-------|
| `DATABASE_URL` | The Supabase connection string. |

## Authentication Configuration
The `staticwebapp.config.json` is configured to use Entra ID (`aad`) and GitHub.
Ensure the Static Web App has been configured with these identity providers if custom registrations are required. For "Basic" tier, GitHub is usually automatic, but Entra ID may require setup if using a specific tenant.
