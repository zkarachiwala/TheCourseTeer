# Azure Deployment Configuration Notes

## GitHub Secrets
The following secrets must be configured in the GitHub repository (Settings > Secrets and variables > Actions):

| Secret Name | Description |
|-------------|-------------|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | The deployment token for the Azure Static Web App (obtained from Azure Portal). |
| `DATABASE_URL` | The Supabase connection string (transaction pooler). |

## Azure Static Web App Environment Variables
Configure these in the Azure Portal (Static Web App > Configuration):

| Variable Name | Value |
|---------------|-------|
| `DATABASE_URL` | The Supabase connection string. |

## Authentication Configuration
The `staticwebapp.config.json` is configured to use Entra ID (`aad`) and GitHub.
Ensure the Static Web App has been configured with these identity providers if custom registrations are required. For "Basic" tier, GitHub is usually automatic, but Entra ID may require setup if using a specific tenant.
