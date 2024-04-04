import streamlit as st
from transformers import pipeline
from youtube_transcript_api import YouTubeTranscriptApi
import mysql.connector

# Function to connect to MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Add your MySQL password
        database="video_summaries"  # Replace with your database name
    )

# Function to insert video URL and summary into MySQL database
def insert_to_database(video_url, summary):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Insert data into the database
        sql = "INSERT INTO video_summaries (video_url, summary) VALUES (%s, %s)"
        val = (video_url, summary)
        cursor.execute(sql, val)

        conn.commit()
        st.success("Data inserted into the database successfully.")

    except mysql.connector.Error as e:
        st.error(f"Error inserting data into the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def load_summarizer():
    try:
        model = pipeline("summarization", device=-1)  # Specify device=-1 to use CPU
        return model
    except Exception as e:
        # Suppress the warning
        pass

def generate_chunks(inp_str, max_chunk_size=500):
    chunks = [inp_str[i:i+max_chunk_size] for i in range(0, len(inp_str), max_chunk_size)]
    return chunks

def get_transcript(video_url):
    video_id = video_url.split("v=")[1]
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = ' '.join([t['text'] for t in transcript_list])
        return transcript
    except Exception as e:
        st.error("Failed to fetch transcript. Please check the video URL or try again later.")
        st.error(e)
        return None

# Streamlit app
st.title("Summarize YouTube Video")
video_url = st.text_input("Please enter the YouTube video URL:")
button = st.button("Summarize")

if button and video_url:
    transcript = get_transcript(video_url)
    if transcript:
        summarizer = load_summarizer()
        
        with st.spinner("Generating Summary.."):
            chunks = generate_chunks(transcript)
            res = summarizer(chunks)
            text = ' '.join([summ['summary_text'] for summ in res])
            st.write(text)
            
            # Insert video URL and summary into the database
            insert_to_database(video_url, text)
