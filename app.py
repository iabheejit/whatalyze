import streamlit as st
from utils import (
    parse_chat, 
    filter_chat, 
    analyze_chat, 
    create_wordcloud, 
    plot_emoji_analysis, 
    plot_activity_by_hour, 
    plot_activity_by_weekday, 
    plot_messages_by_sender, 
    plot_messages_timeline, 
    display_analysis, 
    load_and_cache_data
)
from azure_client import generate_ai_insights, ai_chat_analysis

def main():
    st.markdown("""
        <div style="width: 100%; height: 250px; display: flex; justify-content: center; align-items: center; border: 5px solid #000; box-sizing: border-box;">
            <div style="width: 100%; height: 100%; display: flex; justify-content: center; align-items: center;">
                <img src="https://github.com/iabheejit/whatalyze/blob/main/header.jpg?raw=true" alt="Header Image" style="max-width: 100%; max-height: 100%; object-fit: contain;"/>
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

if __name__ == "__main__":
    main()
