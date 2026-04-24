# Cloud Native Poster Submission System (Mini Project 1)

## Overview

A hybrid cloud poster submission system with **3 container services** (AWS EC2) and **3 serverless functions** (Alibaba Cloud). Users submit posters; the system validates input and returns **READY / NEEDS_REVISION / INCOMPLETE**.

## Architecture
User → Presentation → Workflow → Submission Event → Processing → Result Update → Data Service → User

| Component | Type | Platform | Role |
|-----------|------|----------|------|
| Presentation | Container | AWS EC2 | Frontend UI |
| Workflow | Container | AWS EC2 | Orchestration |
| Data Service | Container | AWS EC2 | Storage |
| Submission Event | Serverless | Alibaba Cloud | Entry point |
| Processing | Serverless | Alibaba Cloud | Business logic |
| Result Update | Serverless | Alibaba Cloud | Update storage |

## Business Rules

| Condition | Status |
|-----------|--------|
| Missing title/description/filename | **INCOMPLETE** |
| Description < 30 chars OR invalid extension (.jpg/.jpeg/.png required) | **NEEDS REVISION** |
| All valid | **READY** |

## My Contribution (3 Serverless Functions)

### Functions

| Function | Handler | Role |
|----------|---------|------|
| Submission Event | `SubmissionEventHandler::handleRequest` | Receive requests, trigger processing |
| Processing | `ProcessingHandler::handleRequest` | Apply business rules, compute status |
| Result Update | `ResultUpdateHandler::handleRequest` | Update Data Service via PUT |

### Environment Variables (Alibaba Cloud Console)

| Function | Variable | Value |
|----------|----------|-------|
| Submission Event | `PROCESSING_FUNCTION_URL` | Processing function URL |
| Processing | `RESULT_UPDATE_FUNCTION_URL` | Result Update function URL |
| Result Update | `DATA_SERVICE_URL` | `http://54.252.166.148:5002` |

### Deployment

```bash
# Build
mvn clean package

# Upload group-project-1.0-SNAPSHOT.jar to Alibaba Cloud Function Compute
# Configure Handler and environment variables
# Create HTTP trigger (POST, no auth)


Repository
https://github.com/OptimusHimself/mini-project-1

Video
https://share.weiyun.com/4t5Oc1Gs

Report
COMP3006J_21_22207668.pdf
