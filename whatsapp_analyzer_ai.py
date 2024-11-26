import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
from collections import Counter
import emoji
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

# Import Azure OpenAI for advanced analysis
from openai import AzureOpenAI

# Configuration for Azure OpenAI
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY_0m","")
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
        st.error(f"Error initializing Azure OpenAI client: {str(e)}")
        return None

# Function to parse chat messages
@st.cache_data
def parse_chat(text):
    pattern = r'\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]?\s*-\s*([^:]+):\s*(.*)'

    messages = []
    unmatched_lines = 0

    for line in text.split('\n'):
        if not line:
            continue
        match = re.match(pattern, line)
        if match:
            date, time, sender, message = match.groups()
            
            try:
                if len(date.split('/')[-1]) == 2:
                    date = date.replace(date.split('/')[-1], '20' + date.split('/')[-1])
                
                datetime_str = f"{date} {time}"
                date_formats = [
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y %H:%M',
                    '%d/%m/%Y %I:%M %p',
                    '%m/%d/%Y %H:%M:%S',
                    '%m/%d/%Y %H:%M',
                    '%m/%d/%Y %I:%M %p'
                ]

                for fmt in date_formats:
                    try:
                        dt = datetime.strptime(datetime_str, fmt)
                        break
                    except ValueError:
                        continue

                messages.append({
                    'datetime': dt,
                    'date': dt.date(),
                    'time': dt.time(),
                    'sender': sender.strip(),
                    'message': message.strip()
                })
            except Exception as e:
                unmatched_lines += 1
                continue

    df = pd.DataFrame(messages)
    df = df.sort_values(by='datetime').reset_index(drop=True)
    return df, unmatched_lines

# Function to filter chat messages based on sender and date range
@st.cache_data
def filter_chat(df, sender=None, start_date=None, end_date=None):
    if sender:
        df = df[df['sender'] == sender]
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date).date()]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date).date()]
    return df

# Function to analyze the chat data
@st.cache_data
def analyze_chat(df):
    total_messages = len(df)
    total_days = (df['date'].max() - df['date'].min()).days
    avg_messages_per_day = total_messages / total_days if total_days > 0 else 0

    # Messages by sender
    messages_by_sender = df['sender'].value_counts()

    # Messages by date
    messages_by_date = df.groupby('date').size()

    # Messages by hour
    df['hour'] = df['datetime'].dt.hour
    messages_by_hour = df.groupby('hour').size()

    # Messages by weekday
    df['weekday'] = df['datetime'].dt.day_name()
    messages_by_weekday = df.groupby('weekday').size()

    # Word count
    df['word_count'] = df['message'].str.split().str.len()
    words_per_message = df['word_count'].mean()

    # Emoji analysis
    all_emojis = [char for message in df['message'] for char in message if emoji.is_emoji(char)]
    most_common_emojis = Counter(all_emojis).most_common(10)

    return {
        'total_messages': total_messages,
        'total_days': total_days,
        'avg_messages_per_day': avg_messages_per_day,
        'messages_by_sender': messages_by_sender,
        'messages_by_date': messages_by_date,
        'messages_by_hour': messages_by_hour,
        'messages_by_weekday': messages_by_weekday,
        'words_per_message': words_per_message,
        'most_common_emojis': most_common_emojis
    }

# Create a word cloud from the chat messages
def create_wordcloud(df):
    all_messages = ' '.join(df['message'].astype(str))
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_messages)
    return wordcloud

# Plot the emoji analysis
def plot_emoji_analysis(analysis):
    st.header("Top Emojis Used")
    emoji_labels, emoji_counts = zip(*analysis['most_common_emojis'])
    fig_emojis = px.bar(x=emoji_labels, y=emoji_counts, title="Most Used Emojis")
    st.plotly_chart(fig_emojis)

# Plot activity by hour
def plot_activity_by_hour(analysis):
    st.header("Activity by Hour")
    fig_hour = px.bar(x=analysis['messages_by_hour'].index,
                      y=analysis['messages_by_hour'].values,
                      title="Messages by Hour of Day")
    st.plotly_chart(fig_hour)

# Plot activity by weekday
def plot_activity_by_weekday(analysis):
    st.header("Activity by Weekday")
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_counts = analysis['messages_by_weekday'].reindex(weekday_order)
    fig_weekday = px.bar(x=weekday_counts.index,
                         y=weekday_counts.values,
                         title="Messages by Day of Week")
    st.plotly_chart(fig_weekday)

# Plot messages by sender
def plot_messages_by_sender(analysis):
    st.header("Message Distribution by Sender")
    # Filter out senders with less than 2% of total messages
    total_messages = analysis['total_messages']
    sender_data = analysis['messages_by_sender']
    
    # Calculate the percentage of total messages for each sender
    sender_percent = (sender_data / total_messages) * 100
    
    # Filter to include only senders with at least 2% of total messages
    filtered_senders = sender_data[sender_percent >= 2]

    # Create a pie chart with the filtered senders
    fig = px.pie(
        names=filtered_senders.index,
        values=filtered_senders.values,
    )
    st.plotly_chart(fig)

# Plot messages timeline
def plot_messages_timeline(analysis):
    st.header("Messages Timeline")
    fig_timeline = px.line(x=analysis['messages_by_date'].index,
                           y=analysis['messages_by_date'].values,
                           title="Messages per Day")
    st.plotly_chart(fig_timeline)

# Display analysis
# Display analysis with filtered data
def display_analysis(filtered_df, analysis):
    # Display basic stats
    st.header("Chat Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Messages", analysis['total_messages'])
    with col2:
        st.metric("Total Days", analysis['total_days'])
    with col3:
        st.metric("Avg Messages/Day", f"{analysis['avg_messages_per_day']:.1f}")

    # Plot charts
    plot_messages_by_sender(analysis)
    plot_messages_timeline(analysis)
    plot_activity_by_hour(analysis)
    plot_activity_by_weekday(analysis)
    plot_emoji_analysis(analysis)

    # Word Cloud
    st.header("Word Cloud")
    wordcloud = create_wordcloud(filtered_df)  # Pass filtered_df here
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

# NEW: AI-powered advanced analysis function
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
                    "content": f"Prove a well formatted and detailed response, based on the following chat data summary, identify key insights, trends, and communication dynamics. Provide unique and actionable observations:\n\n{context}\n\nSpecifically address:\n1. Significant patterns in communication frequency or timing.\n2. Indicators of relationship dynamics (e.g., dominant or passive communicators).\n3. Changes in tone, sentiment, or emotional patterns over time.\n4. Any notable or unusual behaviors or anomalies in the data.\n5. Opportunities to improve communication based on the trends observed."
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating AI insights: {str(e)}"

# NEW: AI Chatbot function for conversational analysis
def ai_chat_analysis(df, user_query):
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

# Modified main function to include AI components
def main():
    st.markdown("""
        <div style="width: 100%; height: 250px; display: flex; justify-content: center; align-items: center; border: 5px solid #000; box-sizing: border-box;">
            <div style="width: 100%; height: 100%; display: flex; justify-content: center; align-items: center;">
                <img src="https://static.vecteezy.com/ti/gratis-vektor/p1/8689741-datenanalyse-banner-web-symbol-analyse-data-mining-datenfilter-kreisdiagramm-prasentation-datenbank-flussdiagramm-rechner-illustration-konzept-vektor.jpg" alt="Header Image" style="max-width: 100%; max-height: 100%; object-fit: contain;"/>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.title("Advanced WhatsApp Chat Analyzer")
    st.write("Upload your WhatsApp chat export file (in `.txt` format) for comprehensive analysis.")

    uploaded_file = st.file_uploader("Choose a file", type=['txt'])

    if uploaded_file:
        # Load and cache the chat data
        df = load_and_cache_data(uploaded_file)
        unmatched_lines = st.session_state.unmatched_lines

        if unmatched_lines > 0:
            st.warning(f"Couldn't parse {unmatched_lines} lines. Please check the format.")

        if len(df) > 0:
            # Add filters for Sender and Date range
            st.sidebar.header("Filters")
            sender_filter = st.sidebar.selectbox("Select Sender", options=["All"] + list(df['sender'].unique()))
            start_date = st.sidebar.date_input("Start Date", df['date'].min())
            end_date = st.sidebar.date_input("End Date", df['date'].max())

            filtered_df = filter_chat(df, sender=sender_filter if sender_filter != "All" else None, 
                                      start_date=start_date, end_date=end_date)

            # Update analysis based on filtered data
            filtered_analysis = analyze_chat(filtered_df)

            # Display analysis with filtered data
            display_analysis(filtered_df, filtered_analysis)

            # NEW: AI-Powered Insights Section
            st.header("🤖 AI-Powered Insights")
            with st.spinner('Generating advanced insights...'):
                ai_insights = generate_ai_insights(filtered_df)
                st.write(ai_insights)

            # NEW: AI Chat Interface
            st.header("💬 Chat with Your Data")
            user_query = st.text_input("Ask a question about your chat data:")
            
            if user_query:
                with st.spinner('Analyzing your query...'):
                    ai_response = ai_chat_analysis(filtered_df, user_query)
                    st.markdown(f"**Response:** {ai_response}")
                      
        else:
            st.error("No messages found in the file. Please check the format.")

# Function to cache data
def load_and_cache_data(uploaded_file):
    if 'df' not in st.session_state:
        text = uploaded_file.getvalue().decode('utf-8')
        df, unmatched_lines = parse_chat(text)
        st.session_state.df = df
        st.session_state.unmatched_lines = unmatched_lines
    return st.session_state.df

if __name__ == "__main__":
    main()
