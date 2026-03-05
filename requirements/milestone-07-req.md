# Milestone v0.7 - API Service & MCP

## Overview
This milestone introduces API-based integrations with third-party services to extend Spectra's functionality. The focus is on providing a flexible, secure, and scalable integration framework that allows users to connect external services to their Spectra workflows.

## 1. API Key Management Requirements

### 1.1 Consumer API Keys from Spetra Frontend

- User can manage their own API keys from the Settings menu on Spectra Settings/API Keys page
- User can list their API keys 
- User can create API keys with a name and description
- User can revoke their API keys

### 1.2 Admin API Keys Management from Spectra Admin Fronten

- Admin can manage API keys for all users from the User Management page
- Admin can list API keys for all users
- Admin can create API keys for users
- Admin can revoke API keys for users

### 1.3 API Security
- API keys are stored securely in the database
- Every API call must include the API key in the header for authentication
- Revoked API keys cannot be used for authentication

### 1.4 API Usage Tracking

- API call may impact user credits (Details to be determined for each use case)
- API cost is according to the existing credit cost configuration (e.g., 1 credit per message sent)
- Track API usage per user and per API key and capture the log 

## 2. API Use Cases Requirements

### 2.1 File Management
- Upload data source in the form of CSV or Excel File Object. This will trigger the on-boarding process to generate the Data Brief, Summary and Query Suggestions
- List all files uploaded by the user
- Delete files uploaded by the user
- Get/download file uploaded by the user

### 2.2 File Context
- Get file detail including Data Brief, Summary and Context
- Update file Data Summary or Context
- Get query suggestions for the file

### 2.3 Chat   
- Chat (Query) from a data file, this will return the Code, Visualization and Analysis summary

## 3. API Infrastructure Requirements
- API to be exposed as a separate service and can be accessed via HTTPS which is different than the existing Backend API service
- The service should be scalable and able to handle a large number of API calls
- The service should be able to handle API rate limiting and throttling (Subject for discussion - could be deferred to later)
- The service should be secure and able to handle authentication
- The service should be able to handle API versioning
- The service should be able to handle API monitoring and logging


## 4. MCP Server Requirements
- Create an MCP server that exposes the API endpoints as tools for AI agents to use (Detail to be discussed)

