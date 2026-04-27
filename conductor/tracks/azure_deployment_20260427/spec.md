# Specification: Azure Deployment for The Courseteer Web App

## Overview
Deploy the Next.js front-end web application of The Courseteer to Azure Static Web Apps. The deployment will be hosted in the `The ZZone Development Subscription` tenant, specifically within the `TheCourseteerDev` resource group. The configuration should follow the reference deployment pattern previously used in the "mobilehub" app.

## Scope
- **In Scope:**
  - Configuration and deployment of the Next.js web app (`/web` directory) to Azure Static Web Apps.
  - Implementation of basic authentication using Microsoft Entra ID and GitHub.
  - Environment variable configuration to connect to the existing Supabase PostgreSQL instance.
- **Out of Scope:**
  - Deployment of the Python scraper/Playwright backend components.
  - Provisioning of new database infrastructure (continuing to use existing Supabase).

## Functional Requirements
- **Hosting:** The Next.js application must be deployed as an Azure Static Web App.
- **Authentication:** Users must be able to authenticate using Microsoft Entra ID or GitHub.
- **Database Connection:** The web app must successfully connect to the existing Supabase instance for data operations.

## Non-Functional Requirements
- **Resource Group:** All resources must be placed in the `TheCourseteerDev` resource group.
- **Subscription:** The deployment must target `The ZZone Development Subscription`.
- **Infrastructure:** The deployment configuration should be structured for repeatable setup, similar to the mobilehub app reference.

## Acceptance Criteria
- [ ] The Next.js web application is accessible via an Azure Static Web Apps URL.
- [ ] Users can successfully log in using Entra ID.
- [ ] Users can successfully log in using GitHub.
- [ ] The web app correctly reads data from the existing Supabase database.