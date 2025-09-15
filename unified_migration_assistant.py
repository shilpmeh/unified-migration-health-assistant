import streamlit as st
import boto3
import json
from datetime import datetime
import hashlib

# Configure page
st.set_page_config(
    page_title="Migration Health AI Assistant",
    page_icon="🏥",
    layout="wide"
)

# Authentication
def check_password():
    """Returns `True` if the user had the correct password."""
    # Hardcoded for testing - password is "test123"
    TEST_PASSWORD_HASH = "ecd71870d1963316a97e3ac3408c9835ad8cf0f3c1bc703527c30265534f75ae"
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        entered_hash = hashlib.sha256(st.session_state["password"].encode()).hexdigest()
        
        if entered_hash == TEST_PASSWORD_HASH:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Return True if password is validated
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize Bedrock client
@st.cache_resource
def get_bedrock_client():
    # Use default AWS credentials (from ~/.aws/credentials or IAM role)
    return boto3.client('bedrock-agent-runtime', region_name='us-east-1')

def validate_input(query):
    """Validate user input for security"""
    # Only validate user input length (not system prompt)
    if len(query) > 500:  # Reasonable limit for user queries
        return False, "Query too long (max 500 characters)"
    
    # Block potential injection attempts
    blocked_patterns = ['<script', 'javascript:', 'eval(', 'exec(']
    if any(pattern in query.lower() for pattern in blocked_patterns):
        return False, "Invalid input detected"
    
    return True, ""

def query_knowledge_base(user_query, kb_id):
    """Query Bedrock knowledge base with security checks"""
    # Validate only the user input, not the system prompt
    is_valid, error_msg = validate_input(user_query)
    if not is_valid:
        return f"Security Error: {error_msg}"
    
    # Make the query more specific to retrieve actual data
    enhanced_query = f"""COMPREHENSIVE DATA RETRIEVAL REQUEST:

Query: {user_query}

CRITICAL INSTRUCTIONS:
1. Search ALL available data sources and files
2. Retrieve COMPLETE datasets, not just summaries  
3. Include ALL relevant rows and columns of data
4. Provide specific numbers, names, and details from the actual files
5. Show real data from Detailed_Report, YTD_Revenue_Progress, Pipeline_Detail, and ARR_Win_Deal sheets
6. Include actual customer names, engagement IDs, revenue figures, health statuses
7. Format data in tables when showing lists or comparisons

{SYSTEM_PROMPT}"""
    
    try:
        client = get_bedrock_client()
        response = client.retrieve_and_generate(
            input={'text': enhanced_query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_id,
                    'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 20,  # Increase from default (usually 5)
                            'overrideSearchType': 'HYBRID'  # Use both semantic and keyword search
                        }
                    }
                }
            }
        )
        return response['output']['text']
    except Exception as e:
        # Show actual error for debugging
        st.error(f"Debug Error: {str(e)}")
        return f"Error details: {str(e)}"

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
SYSTEM_PROMPT = """You are a Migration Health AI Assistant. 

IMPORTANT: Always retrieve and analyze actual data from the knowledge base files (Excel sheets, JSON files, PDFs). Do not provide generic responses.

Data Sources to query:
- Detailed_Report: Migration status, customer info, revenue data
- YTD_Revenue_Progress: Revenue tracking and partner data  
- Pipeline_Detail: Pipeline opportunities (only for pipeline queries)
- ARR_Win_Deal: Deal data (only for pipeline queries)

For "Show" or "List" queries, provide data in tabular format.
Always use actual data from the files, never hypothetical examples."""

# Main UI
st.title("🏥 Migration Health AI Assistant")
st.markdown("*AWS HCLS Migration & Modernization Analysis*")

# Knowledge Base ID - hardcoded
kb_id = "HBNUJXVNB8"

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
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing migration data..."):
            # Pass only user query, system prompt will be added inside the function
            response = query_knowledge_base(user_query, kb_id)
            
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
