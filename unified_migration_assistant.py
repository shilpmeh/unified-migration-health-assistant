import streamlit as st
import boto3
import json
import uuid

# Configure page
st.set_page_config(page_title="HCLS Migration Health Assistant", page_icon="🏥", layout="wide")
st.title("🏥 HCLS Migration Health Assistant")

# Initialize AWS clients
@st.cache_resource
def get_aws_clients():
    return {
        'bedrock': boto3.client('bedrock-agent-runtime', region_name='us-east-1'),
        'qbusiness': boto3.client('qbusiness', region_name='us-east-1')
    }

clients = get_aws_clients()

# Configuration
KB_ID = "HBNUJXVNB8"  # Bedrock Knowledge Base
QBUSINESS_APP_ID = "71fee8c3-d898-4d1b-b70a-c624128d7028"  # Q Business App
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"

def query_bedrock_kb(query):
    """Query Bedrock Knowledge Base"""
    try:
        response = clients['bedrock'].retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KB_ID,
                    'modelArn': MODEL_ARN,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 20
                        }
                    }
                }
            }
        )
        
        return {
            'answer': response['output']['text'],
            'sources': response.get('citations', [])
        }
    except Exception as e:
        return {
            'answer': f"Error querying knowledge base: {str(e)}",
            'sources': []
        }

def process_query(prompt):
    """Process a query and add to chat"""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process query
    result = query_bedrock_kb(prompt)
    st.session_state.messages.append({
        "role": "assistant", 
        "content": result['answer'],
        "sources": result['sources']
    })

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar with sample queries
with st.sidebar:
    st.header("💡 Sample Queries")
    
    sample_queries = [
        "Show migration status for ModivCare",
        "What is the current YTD revenue realization vs target?",
        "List all partner-attached migrations and their performance",
        "Which migrations have high spend variance?",
        "Calculate revenue attainment for Q3",
        "Identify at-risk migrations",
        "Partner performance analysis",
        "Show migration health status by territory"
    ]
    
    for i, query in enumerate(sample_queries):
        if st.button(query, key=f"sample_{i}"):
            process_query(query)
            st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"][:3]):
                    if isinstance(source, dict):
                        st.write(f"**Source {i+1}:** {source.get('generatedResponsePart', {}).get('textResponsePart', {}).get('text', 'N/A')}")
                    else:
                        st.write(f"**Source {i+1}:** {source}")

# Chat input
if prompt := st.chat_input("Ask about migration health data..."):
    with st.spinner("Analyzing migration data..."):
        process_query(prompt)
        st.rerun()
