# Implementation Plan: Azure Deployment for The Courseteer Web App

## Phase 1: Setup and Configuration [checkpoint: 547bfca]
- [x] Task: Create Azure Static Web App configuration (`staticwebapp.config.json`) in the `/web` directory to handle routes, authentication, and fallback for Next.js. 39ff370
- [x] Task: Configure Authentication settings within `staticwebapp.config.json` for Entra ID (`aad`) and GitHub. 6bfc430
- [x] Task: Define GitHub Actions workflow file (`.github/workflows/azure-static-web-apps.yml`) for continuous deployment to Azure. 2d64071
- [x] Task: Document required environment variables (Supabase URL/Keys) for injection into Azure/GitHub Actions secrets. 8f30642
- [x] Task: Conductor - User Manual Verification 'Phase 1: Setup and Configuration' (Protocol in workflow.md) 547bfca

## Phase 2: Deployment and Validation [checkpoint: 2a08020]
- [x] Task: Provision the Azure Static Web App resource in the `TheCourseteerDev` resource group within `The ZZone Development Subscription`.
- [x] Task: Link the Azure Static Web App to the GitHub repository to trigger the initial deployment workflow.
- [x] Task: Configure required environment variables in the Azure Static Web App settings.
- [x] Task: Verify successful deployment, including Entra ID login, GitHub login, and database connectivity. 613aedd
- [x] Task: Conductor - User Manual Verification 'Phase 2: Deployment and Validation' (Protocol in workflow.md) 2a08020