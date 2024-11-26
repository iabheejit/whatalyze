import streamlit as st
from openai import AzureOpenAI
import os

# Configuration for Azure OpenAI
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY_0m", "")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT_0m", "")
DEPLOYMENT_NAME = os.environ.get("DEPLOYMENT_NAME_0m", "")
API_VERSION = os.environ.get("API_VERSION_0m", "")

# Initialize Azure OpenAI client
def get_azure_client():
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        return client
    except Exception as e:
        print(f"Error initializing Azure OpenAI client: {str(e)}")
        return None

# Function to generate AI insights
def generate_ai_insights(df):
    """
    Generate advanced insights using Azure OpenAI
    """
    client = get_azure_client()
    if not client:
        return "AI insights unavailable"

    # Prepare context for AI analysis
    context = f"""
    Chat Analysis Summary:
    - Total Messages: {len(df)}
    - Date Range: {df['date'].min()} to {df['date'].max()}
    - Unique Senders: {df['sender'].nunique()}
    
    Sender Message Distribution:
    {df['sender'].value_counts().to_string()}
    
    Top 5 Most Active Dates:
    {df.groupby('date').size().nlargest(5).to_string()}
    """

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are an advanced conversational analyst with expertise in understanding human communication patterns. Your goal is to provide profound, data-driven, and actionable insights into communication behaviors, relationship dynamics, and meaningful trends observed in the chat data summary. Focus on uncovering subtle patterns, anomalies, and potential areas for improvement or celebration in the communication."
                },
                {
                    "role": "user",
                    "content": f"Prove a well formatted and detailed response under 500 words, based on the following chat data summary, identify key insights, trends, and communication dynamics. Provide unique and actionable observations:\n\n{context}\n\nSpecifically address:\n1. Significant patterns in communication frequency or timing.\n2. Indicators of relationship dynamics (e.g., dominant or passive communicators).\n3. Changes in tone, sentiment, or emotional patterns over time.\n4. Any notable or unusual behaviors or anomalies in the data.\n5. Opportunities to improve communication based on the trends observed."
                }
            ],
            max_tokens=800,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating AI insights: {str(e)}"

# NEW: AI Chatbot function for conversational analysis
def ai_chat_analysis(filtered_df, user_query):
    """
    Generate conversational responses about the chat data
    """
    client = get_azure_client()
    if not client:
        return "AI chat unavailable"

    # Prepare context with some key chat statistics
    context = f"""
    Chat Context:
    - Total Messages: {len(df)}
    - Date Range: {df['date'].min()} to {df['date'].max()}
    - Unique Senders: {df['sender'].nunique()}
    - Average Messages per Day: {len(df) / ((df['date'].max() - df['date'].min()).days + 1):.2f}
    
    Sender Message Distribution:
    {df['sender'].value_counts().to_string()}
    """

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert chat data analyst. Provide detailed, data-driven responses about the chat based on the provided context. Always ground your answers in the actual data."
                },
                {
                    "role": "user", 
                    "content": f"Context:\n{context}\n\nUser Query: {user_query}"
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error in chat analysis: {str(e)}"
