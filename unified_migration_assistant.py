import streamlit as st
import boto3
import json

# Configure page
st.set_page_config(page_title="Unified Migration Health Assistant", page_icon="🏥", layout="wide")
st.title("🏥 Unified Migration Health Assistant")

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

# Query routing logic
def route_query(query):
    """Route queries to appropriate system based on content"""
    query_lower = query.lower()
    
    # Q Business keywords (structured data analysis)
    qbusiness_keywords = [
        'territory', 'sfdc customer', 'revenue realization', 'partner performance',
        'migration status', 'detailed report', 'ytd revenue', 'spend variance',
        'customer territory code', 'engagement id', 'migration delivered by'
    ]
    
    # Bedrock KB keywords (semantic search)
    bedrock_keywords = [
        'explain', 'how to', 'what is', 'describe', 'summary', 'overview',
        'best practices', 'recommendations', 'challenges', 'insights'
    ]
    
    qbusiness_score = sum(1 for keyword in qbusiness_keywords if keyword in query_lower)
    bedrock_score = sum(1 for keyword in bedrock_keywords if keyword in query_lower)
    
    if qbusiness_score > bedrock_score:
        return 'qbusiness'
    elif bedrock_score > qbusiness_score:
        return 'bedrock'
    else:
        return 'both'  # Use both for comprehensive analysis

def query_qbusiness(query):
    """Query Q Business application"""
    try:
        response = clients['qbusiness'].chat_sync(
            applicationId=QBUSINESS_APP_ID,
            userMessage=query,
            conversationId=st.session_state.get('qbusiness_conversation_id')
        )
        
        # Store conversation ID for context
        if 'conversationId' in response:
            st.session_state.qbusiness_conversation_id = response['conversationId']
        
        return {
            'source': 'Q Business',
            'answer': response.get('systemMessage', 'No response'),
            'sources': response.get('sourceAttributions', [])
        }
    except Exception as e:
        return {
            'source': 'Q Business',
            'answer': f"Error: {str(e)}",
            'sources': []
        }

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
                            'numberOfResults': 10
                        }
                    }
                }
            }
        )
        
        return {
            'source': 'Bedrock Knowledge Base',
            'answer': response['output']['text'],
            'sources': response.get('citations', [])
        }
    except Exception as e:
        return {
            'source': 'Bedrock Knowledge Base',
            'answer': f"Error: {str(e)}",
            'sources': []
        }

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"][:3]):
                    st.write(f"**Source {i+1}:** {source}")

# Chat input
if prompt := st.chat_input("Ask about migration health data..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Route and process query
    with st.chat_message("assistant"):
        with st.spinner("Analyzing migration data..."):
            route = route_query(prompt)
            
            if route == 'qbusiness':
                result = query_qbusiness(prompt)
                st.markdown(f"**{result['source']}:**\n\n{result['answer']}")
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"**{result['source']}:**\n\n{result['answer']}",
                    "sources": result['sources']
                })
                
            elif route == 'bedrock':
                result = query_bedrock_kb(prompt)
                st.markdown(f"**{result['source']}:**\n\n{result['answer']}")
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"**{result['source']}:**\n\n{result['answer']}",
                    "sources": result['sources']
                })
                
            else:  # both
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Q Business Analysis")
                    qb_result = query_qbusiness(prompt)
                    st.markdown(qb_result['answer'])
                
                with col2:
                    st.subheader("🔍 Knowledge Base Insights")
                    kb_result = query_bedrock_kb(prompt)
                    st.markdown(kb_result['answer'])
                
                combined_answer = f"**Q Business Analysis:**\n{qb_result['answer']}\n\n**Knowledge Base Insights:**\n{kb_result['answer']}"
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": combined_answer,
                    "sources": qb_result['sources'] + kb_result['sources']
                })

# Sidebar with routing info and sample queries
with st.sidebar:
    st.header("🎯 Query Routing")
    st.info("""
    **Q Business** - For structured data:
    • Territory analysis
    • Revenue metrics
    • Partner performance
    • Migration status
    
    **Bedrock KB** - For insights:
    • Explanations
    • Best practices
    • Recommendations
    • Overviews
    
    **Both** - For comprehensive analysis
    """)
    
    st.header("💡 Sample Queries")
    
    st.subheader("Q Business Queries")
    qb_queries = [
        "Show migration status by customer territory code",
        "What is the current YTD revenue realization vs target?",
        "List all partner-attached migrations and their performance"
    ]
    
    for query in qb_queries:
        if st.button(query, key=f"qb_{query}"):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()
    
    st.subheader("Bedrock KB Queries")
    kb_queries = [
        "Explain migration health best practices",
        "What are common migration challenges?",
        "Describe revenue optimization strategies"
    ]
    
    for query in kb_queries:
        if st.button(query, key=f"kb_{query}"):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()
    
    st.subheader("Combined Analysis")
    combined_queries = [
        "Analyze overall migration performance and suggest improvements",
        "What insights can you provide about our migration portfolio?"
    ]
    
    for query in combined_queries:
        if st.button(query, key=f"combined_{query}"):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()
