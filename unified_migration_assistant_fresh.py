import streamlit as st
import boto3
import json
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Migration Health AI Assistant",
    page_icon="🏥",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize Bedrock client
@st.cache_resource
def get_bedrock_client():
    # Try to use Streamlit secrets first, fallback to local AWS config
    try:
        return boto3.client(
            'bedrock-agent-runtime',
            region_name='us-east-1',
            aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
        )
    except:
        return boto3.client('bedrock-agent-runtime', region_name='us-east-1')

def query_knowledge_base(query, kb_id):
    """Query Bedrock knowledge base"""
    try:
        client = get_bedrock_client()
        response = client.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_id,
                    'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
                }
            }
        )
        return response['output']['text']
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"

def format_tabular_response(response_text):
    """Format response as table if it contains tabular data"""
    lines = response_text.split('\n')
    table_data = []
    headers = []
    
    for line in lines:
        if '|' in line and line.strip():
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                if not headers:
                    headers = cells
                else:
                    table_data.append(cells)
    
    if headers and table_data:
        try:
            import pandas as pd
            df = pd.DataFrame(table_data, columns=headers)
            return df
        except:
            pass
    
    return None

# System prompt for the assistant
SYSTEM_PROMPT = """You are the Migration Health AI Assistant for AWS HCLS migration and modernization engagements. 

Your scope includes:
- HCLS customer territory code wise analysis
- SFDC customer name wise migration status analysis and reporting
- Migration status insights including deal type, migration health, revenue realization, partner engagements
- Excel data analysis from YTD_Revenue_Progress and Detailed_Report sheets

Data Sources:
- Detailed_Report: Customer Territory Code, Migration Delivered By, Deal Type, SFDC Customer Name, Engagement ID, Migration Health, Revenue data
- YTD_Revenue_Progress: Partner Engagement, SFDC Customer Name, Engagement ID, Migration Status, Migration ARR
- Pipeline_Detail and ARR_Win_Deal: ONLY for migration pipeline queries

For queries starting with "Show" or "List", provide responses in clear tabular format.
Do not provide hypothetical examples - use only actual data from the knowledge base.
Focus on migration performance analysis, challenge identification, and improvement suggestions."""

# Main UI
st.title("🏥 Migration Health AI Assistant")
st.markdown("*AWS HCLS Migration & Modernization Analysis*")

# Knowledge Base ID - hardcoded
kb_id = "HBNUJXVNB8"
st.info(f"Connected to Knowledge Base: {kb_id}")

# Sample query buttons
st.markdown("### Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 YTD Revenue vs Target"):
        query = "What is the current YTD revenue realization vs target?"
        st.session_state.messages.append({"role": "user", "content": query})
        
    if st.button("🏢 Territory Performance"):
        query = "Show migration distribution by territory"
        st.session_state.messages.append({"role": "user", "content": query})

with col2:
    if st.button("🤝 Partner Analysis"):
        query = "List all partner-attached migrations and their performance"
        st.session_state.messages.append({"role": "user", "content": query})
        
    if st.button("⚠️ High-Risk Migrations"):
        query = "List high-risk migrations"
        st.session_state.messages.append({"role": "user", "content": query})

with col3:
    if st.button("📈 Pipeline Opportunities"):
        query = "Show current pipeline opportunities and their status"
        st.session_state.messages.append({"role": "user", "content": query})
        
    if st.button("🎯 Migration Completion Rates"):
        query = "Show migration completion rates"
        st.session_state.messages.append({"role": "user", "content": query})

# Chat interface
st.markdown("### Chat Interface")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about migration status, revenue, partners, or territories..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

# Process the latest message
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    
    # Enhance query with system context
    enhanced_query = f"{SYSTEM_PROMPT}\n\nUser Query: {user_query}"
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing migration data..."):
            response = query_knowledge_base(enhanced_query, kb_id)
            
            # Check if response should be tabular
            if any(word in user_query.lower() for word in ['show', 'list', 'compare']):
                df = format_tabular_response(response)
                if df is not None:
                    st.dataframe(df, use_container_width=True)
                    st.markdown("---")
                    st.markdown("**Detailed Analysis:**")
            
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with sample queries
with st.sidebar:
    st.markdown("### Sample Queries")
    
    st.markdown("**Account-Specific:**")
    st.code('Show migration status for [SFDC Customer Name]')
    st.code('What are the key challenges for [Customer]?')
    
    st.markdown("**Revenue Performance:**")
    st.code('Which accounts are behind benchmark in revenue?')
    st.code('Show revenue trend for [account name]')
    
    st.markdown("**Partner Analysis:**")
    st.code('Which partners are leading in migration revenue?')
    st.code('Show partner-related execution challenges')
    
    st.markdown("**Territory Analysis:**")
    st.code('Which territories need pipeline growth?')
    st.code('Compare territory performance metrics')
    
    st.markdown("**Risk Assessment:**")
    st.code('Show mitigation plans for at-risk accounts')
    st.code('Provide risk analysis for [account]')

# Footer
st.markdown("---")
st.markdown("*Migration Health AI Assistant - Powered by AWS Bedrock Knowledge Base*")
