---
title: CI/CD
aliases: [CI/CD, CI-CD]
tags: [devops, ci-cd, azure-devops, interview]
order: 14
---

# CI/CD Interview Questions & Answers

> [!info]+ Related Notes
> [[15-Azure-Cloud|Azure Cloud]] · [[16-System-Design|System Design]]

## What is CI/CD?
**Answer:** CI/CD stands for Continuous Integration and Continuous Deployment/Delivery. CI automatically builds and tests code changes, while CD automatically deploys validated changes to production or staging environments.

## What is the difference between Continuous Delivery and Continuous Deployment?
**Answer:** Continuous Delivery means code is always in a deployable state but requires manual approval to deploy to production. Continuous Deployment automatically deploys every change that passes tests directly to production without manual intervention.

## What are the key components of a CI/CD pipeline?
**Answer:**
- Source Control (Git)
- Build Automation
- Automated Testing (Unit, Integration, E2E)
- Artifact Management
- Deployment Automation
- Monitoring and Rollback

## What is Azure DevOps?
**Answer:** Azure DevOps is a Microsoft platform providing CI/CD pipelines, source control (Azure Repos), work tracking (Azure Boards), testing tools, and artifact repositories for end-to-end DevOps workflows.

## What is a YAML pipeline in Azure DevOps?
**Answer:** A YAML pipeline is a pipeline defined as code using YAML syntax. It includes stages, jobs, steps, triggers, and variables, providing version control and reusability.

## What are stages, jobs, and steps in Azure Pipelines?
**Answer:**
- **Stage:** Logical boundary (e.g., Build, Test, Deploy)
- **Job:** Collection of steps running on an agent
- **Step:** Individual task like running a script or command

## What is a build agent?
**Answer:** A build agent is a machine (hosted or self-hosted) that executes pipeline jobs. Microsoft-hosted agents are managed by Azure; self-hosted agents run on your infrastructure.

## How do you handle secrets in CI/CD pipelines?
**Answer:** Use Azure Key Vault or pipeline secret variables. Never hardcode secrets in code. Access them via variable groups or Key Vault tasks with managed identities.

## What is Blue-Green Deployment?
**Answer:** Blue-Green deployment maintains two identical environments (Blue and Green). Traffic switches from Blue (current) to Green (new version) instantly, allowing quick rollback if issues arise.

## What is Canary Deployment?
**Answer:** Canary deployment gradually routes a small percentage of traffic to the new version, monitors performance, and incrementally increases traffic if stable.

## What are deployment slots in Azure App Service?
**Answer:** Deployment slots are separate environments (e.g., staging, production) within an App Service. You can deploy to staging, test, then swap with production with zero downtime.

## What is Infrastructure as Code (IaC)?
**Answer:** IaC manages infrastructure using code (ARM templates, Terraform, Bicep). It ensures consistency, version control, and repeatability.

## What is the purpose of automated testing in CI/CD?
**Answer:** Automated tests catch bugs early, ensure code quality, prevent regressions, and provide confidence before deployment.

## How do you implement rollback strategies?
**Answer:** Use deployment slots, versioned artifacts, feature flags, or infrastructure snapshots. Azure DevOps supports automatic rollback on failed health checks.

## What is GitFlow?
**Answer:** GitFlow is a branching model with main, develop, feature, release, and hotfix branches, providing structured collaboration and release management.

## What are artifacts in CI/CD?
**Answer:** Artifacts are compiled outputs (DLLs, Docker images, ZIP files) produced by the build process and consumed by deployment stages.

## What is Docker in CI/CD context?
**Answer:** Docker containers package applications with dependencies, ensuring consistency across environments. CI/CD pipelines build Docker images, push to registries, and deploy containers.

## What is Kubernetes in CI/CD?
**Answer:** Kubernetes orchestrates containerized applications. CI/CD pipelines deploy updated container images to Kubernetes clusters using Helm charts or kubectl commands.

## What are release gates in Azure Pipelines?
**Answer:** Release gates are automated approval checks (e.g., query Azure Monitor, ServiceNow) before or after deployment stages, ensuring quality and compliance.

## What is trunk-based development?
**Answer:** Trunk-based development commits code directly to the main branch frequently with feature flags, reducing merge conflicts and enabling faster releases.
