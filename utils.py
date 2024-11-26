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
                print(f"Error processing line: {line}. Error: {e}")
                continue

    df = pd.DataFrame(messages)
    if 'datetime' in df.columns:
        df = df.sort_values(by='datetime').reset_index(drop=True)
    else:
        print("Datetime column is missing.")
    
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

# Function to cache data
def load_and_cache_data(uploaded_file):
    if 'df' not in st.session_state:
        text = uploaded_file.getvalue().decode('utf-8')
        df, unmatched_lines = parse_chat(text)
        st.session_state.df = df
        st.session_state.unmatched_lines = unmatched_lines
    return st.session_state.df
