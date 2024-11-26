# Whatalyze

Whatalyze is a project designed to streamline the process of analyzing WhatsApp chat data. It extracts useful insights, trends, and statistics from chat logs, providing an efficient way to process large volumes of chat information for personal or research purposes.

## Features

- **WhatsApp Chat Parsing**: Ability to parse WhatsApp exported chat files.
- **Sentiment Analysis**: Analyze the sentiment of the messages in the chat.
- **Message Frequency Analysis**: Provides insights into message frequency over time.
- **Word Cloud**: Generates word clouds based on the frequency of words used in the chats.
- **Custom Analytics**: Allows for custom analyses on chat data like emoji use, most active users, etc.

## Requirements

- Python 3.6+
- pandas
- matplotlib
- wordcloud
- nltk

## Installation

Clone the repository:

```bash
git clone https://github.com/iabheejit/whatalyze.git
cd whatalyze
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Import the library into your Python environment.
2. Load your WhatsApp chat file:

```python
import whatalyze
chat_data = whatalyze.load_chat('path_to_chat.txt')
```

3. Perform sentiment analysis:

```python
sentiment_analysis = whatalyze.analyze_sentiment(chat_data)
```

4. Generate a word cloud:

```python
whatalyze.generate_wordcloud(chat_data)
```

5. Explore other analytical functions as per your need.

## License

This project is open-source and available under the MIT License.