import re
import pandas as pd
import emoji
from datetime import datetime
from collections import Counter
from wordcloud import WordCloud

# Function to parse chat messages
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
def filter_chat(df, sender=None, start_date=None, end_date=None):
    if sender:
        df = df[df['sender'] == sender]
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date).date()]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date).date()]
    return df

# Function to analyze the chat data
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
