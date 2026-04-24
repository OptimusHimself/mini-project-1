# Cloud Native Poster Submission System (Mini Project 1)

## Overview

A hybrid cloud poster submission system with **3 container services** (AWS EC2) and **3 serverless functions** (Alibaba Cloud). Users submit posters; the system validates input and returns **READY / NEEDS_REVISION / INCOMPLETE**.

- Demo: [Link to video] (to be added)!!这里需要上传视频链接

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




