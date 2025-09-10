# Unified Migration Health Assistant

AI-powered chatbot that combines AWS Q Business and Bedrock Knowledge Base for comprehensive HCLS migration analysis.

## Features

### Smart Query Routing
- **Q Business**: Structured data analysis (territory, revenue, partners)
- **Bedrock KB**: Semantic insights (explanations, best practices)
- **Combined**: Comprehensive analysis using both systems

### Key Capabilities
- Migration portfolio analysis by customer territory
- Revenue realization tracking and forecasting
- Partner performance insights and benchmarking
- Risk identification and mitigation strategies
- Excel-expert data analysis and reporting

## Sample Queries

### Q Business Queries (Structured Data)
- "Show migration status by customer territory code"
- "What is the current YTD revenue realization vs target?"
- "List all partner-attached migrations and their performance"

### Bedrock KB Queries (Insights)
- "Explain migration health best practices"
- "What are common migration challenges?"
- "Describe revenue optimization strategies"

### Combined Analysis
- "Analyze overall migration performance and suggest improvements"
- "What insights can you provide about our migration portfolio?"

## Data Sources
- **Excel Files**: Detailed_Report, YTD_Revenue_Progress, Pipeline_Detail, ARR_Win_Deal
- **Metadata**: JSON files with data structure and usage guidelines
- **Storage**: AWS S3 (csmproductivitytoolsbucket/healthmigration/)

## Architecture
- **Frontend**: Streamlit web application
- **Backend**: AWS Q Business + Bedrock Knowledge Base
- **Vector Storage**: OpenSearch Serverless
- **Authentication**: AWS IAM credentials

## Deployment
Deployed on Streamlit Cloud with AWS integration for enterprise access.
