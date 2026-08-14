---
title: Azure Cloud
aliases: [Azure, Azure Cloud]
tags: [azure, cloud, devops, interview]
order: 15
---

# Azure Cloud Interview Questions & Answers

> [!info]+ Related Notes
> [[14-CI-CD|CI/CD]] · [[16-System-Design|System Design]]

## What is Microsoft Azure?
**Answer:** Azure is Microsoft's cloud computing platform offering IaaS, PaaS, and SaaS services including compute, storage, networking, databases, AI, and DevOps tools.

## What are Azure Regions and Availability Zones?
**Answer:** Azure Regions are geographic locations with data centers. Availability Zones are physically separate data centers within a region, providing high availability and fault tolerance.

## What is Azure App Service?
**Answer:** Azure App Service is a fully managed PaaS for hosting web apps, REST APIs, and mobile backends supporting .NET, Node.js, Python, Java, and PHP with built-in scaling and CI/CD.

## What is Azure Functions?
**Answer:** Azure Functions is a serverless compute service for running event-driven code without managing infrastructure. You pay only for execution time.

## What are the different Azure Function triggers?
**Answer:**
- HTTP Trigger
- Timer Trigger
- Blob Storage Trigger
- Queue Trigger
- Event Grid Trigger
- Service Bus Trigger
- Cosmos DB Trigger

## What is Azure Storage Account?
**Answer:** Azure Storage provides scalable cloud storage with Blob (object), Queue (messaging), Table (NoSQL), and File (SMB) storage services.

## What is the difference between Blob Storage tiers?
**Answer:**
- **Hot:** Frequently accessed data, higher storage cost, lower access cost
- **Cool:** Infrequent access (30+ days), lower storage cost, higher access cost
- **Archive:** Rare access (180+ days), lowest storage cost, highest access cost

## What is Azure SQL Database?
**Answer:** Azure SQL Database is a fully managed relational database (PaaS) based on SQL Server with automatic scaling, backups, patching, and high availability.

## What is Cosmos DB?
**Answer:** Cosmos DB is a globally distributed, multi-model NoSQL database with guaranteed low latency, automatic scaling, and support for SQL, MongoDB, Cassandra, Gremlin, and Table APIs.

## What is Azure Key Vault?
**Answer:** Azure Key Vault securely stores and manages secrets, encryption keys, and certificates with access control, auditing, and integration with Azure services.

## What is Azure Active Directory (Azure AD)?
**Answer:** Azure AD is Microsoft's cloud-based identity and access management service providing authentication, authorization, SSO, and MFA for applications.

## What is Managed Identity in Azure?
**Answer:** Managed Identity provides Azure services with an automatically managed identity in Azure AD, eliminating the need to store credentials in code.

## What are the types of Managed Identities?
**Answer:**
- **System-assigned:** Tied to a single Azure resource lifecycle
- **User-assigned:** Standalone identity resource shared across multiple resources

## What is Azure Service Bus?
**Answer:** Azure Service Bus is a fully managed enterprise message broker supporting queues (point-to-point) and topics (publish-subscribe) with advanced features like sessions and dead-letter queues.

## What is the difference between Azure Service Bus and Azure Storage Queues?
**Answer:** Service Bus supports advanced messaging (topics, sessions, transactions, duplicate detection) while Storage Queues are simpler and cheaper for basic scenarios.

## What is Azure Event Grid?
**Answer:** Azure Event Grid is a fully managed event routing service for building event-driven architectures with reactive programming using publish-subscribe model.

## What is Azure Logic Apps?
**Answer:** Azure Logic Apps is a workflow automation service with visual designer and 200+ connectors for integrating apps, data, and services without code.

## What is Azure API Management?
**Answer:** Azure API Management is a gateway for publishing, securing, transforming, and monitoring APIs with policies, rate limiting, authentication, and developer portal.

## What is Azure Application Insights?
**Answer:** Application Insights is an APM service providing real-time monitoring, distributed tracing, performance metrics, and exception tracking for applications.

## What is Azure Monitor?
**Answer:** Azure Monitor collects, analyzes, and acts on telemetry from Azure resources, providing metrics, logs, alerts, and dashboards.

## What is Azure Virtual Network (VNet)?
**Answer:** Azure VNet is a private network in Azure enabling secure communication between resources with subnets, NSGs, and connectivity to on-premises networks.

## What is Azure Load Balancer?
**Answer:** Azure Load Balancer distributes incoming traffic across healthy VMs at Layer 4 (TCP/UDP) with high availability and low latency.

## What is Azure Application Gateway?
**Answer:** Azure Application Gateway is a Layer 7 load balancer with WAF, SSL termination, URL-based routing, and session affinity for web applications.

## What is Azure Redis Cache?
**Answer:** Azure Cache for Redis is a fully managed in-memory data store for caching, session management, and real-time analytics with high throughput and low latency.

## What is Azure DevOps?
**Answer:** Azure DevOps provides CI/CD pipelines, source control (Repos), work tracking (Boards), testing, and artifact management for end-to-end DevOps.

## What is Azure Container Instances (ACI)?
**Answer:** ACI runs Docker containers on-demand without managing VMs or orchestration, ideal for burst workloads and development/testing.

## What is Azure Kubernetes Service (AKS)?
**Answer:** AKS is a managed Kubernetes service for deploying, scaling, and managing containerized applications with automatic upgrades and monitoring.

## What is Azure Resource Manager (ARM)?
**Answer:** ARM is the deployment and management service for Azure, providing consistent management through templates, RBAC, tags, and resource groups.

## What is an ARM Template?
**Answer:** ARM Template is a JSON file defining infrastructure and configuration declaratively for repeatable, version-controlled deployments (IaC).

## What is Azure Bicep?
**Answer:** Bicep is a domain-specific language for deploying Azure resources with cleaner syntax than ARM templates, compiling to ARM JSON.

## What is RBAC in Azure?
**Answer:** Role-Based Access Control (RBAC) assigns permissions to users, groups, and services at subscription, resource group, or resource levels using built-in or custom roles.

## What is Azure Cost Management?
**Answer:** Azure Cost Management tracks spending, analyzes costs, creates budgets, and provides recommendations for optimizing cloud expenses.

## What is Azure Service Health?
**Answer:** Azure Service Health provides personalized alerts and guidance when Azure service issues affect your resources, including planned maintenance notifications.

## What is Azure Traffic Manager?
**Answer:** Azure Traffic Manager is a DNS-based load balancer distributing traffic across global endpoints using routing methods like priority, weighted, performance, and geographic.

## What is Durable Functions?
**Answer:** Durable Functions is an extension of Azure Functions for writing stateful workflows in code with orchestrations, activities, and entity management.
