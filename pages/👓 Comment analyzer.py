import streamlit as st
import pickle
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from youtube_comment_downloader import YoutubeCommentDownloader
from itertools import islice
from scipy.special import softmax
import mysql.connector

# Connect to MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Change this to your MySQL username
        password="",  # Change this to your MySQL password
        database="sentiment_analysis"  # Change this to your database name
    )

# Function to insert sentiment analysis results into MySQL database
def insert_sentiment_analysis(yturl, no_comment, num_positive, num_negative, num_neutral):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Insert sentiment analysis results into the database
        sql = "INSERT INTO sentiment_analysis_results (yturl, no_comment, num_positive, num_negative, num_neutral) VALUES (%s, %s, %s, %s, %s)"
        val = (yturl, no_comment, num_positive, num_negative, num_neutral)
        cursor.execute(sql, val)

        conn.commit()
        st.success("Sentiment analysis results saved to the database successfully.")

    except mysql.connector.Error as e:
        st.error(f"Error inserting sentiment analysis results into the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def load_sentiment_model():
    with open('C:/Users/admin/Videnhance/pages/sentiment_model_accurate.pickle', 'rb') as file:
        model, tokenizer = pickle.load(file)
    return model, tokenizer

def perform_sentiment_analysis(yturl, no_comment, model, tokenizer):
    downloader = YoutubeCommentDownloader()
    comments = islice(downloader.get_comments_from_url(yturl), no_comment)

    positive_comments = []
    negative_comments = []
    neutral_comments = []

    for comment in comments:
        encoded_comment = tokenizer(comment['text'], return_tensors='pt', padding=True, truncation=True, max_length=512)
        output = model(**encoded_comment)
        scores = output.logits.detach().numpy()[0]
        scores = softmax(scores)

        sentiment_idx = scores.argmax()
        sentiment = labels[sentiment_idx]
        sentiment_prob = scores[sentiment_idx]

        if sentiment == 'Positive':
            positive_comments.append(comment['text'])
        elif sentiment == 'Negative':
            negative_comments.append(comment['text'])
        else:
            neutral_comments.append(comment['text'])

    return positive_comments, negative_comments, neutral_comments

model, tokenizer = load_sentiment_model()

labels = ['Negative', 'Neutral', 'Positive']

st.title("YouTube Comment Analysis Using Roberta Model ")
yturl = st.text_input("Enter YouTube URL:")
no_comment = st.number_input("Enter number of comments:", min_value=1, step=1, value=20)

categorized_comments = None

if yturl != "":
    categorized_comments = perform_sentiment_analysis(yturl, no_comment, model, tokenizer)

if st.button("Analyze"):
    if categorized_comments is not None:
        positive_comments, negative_comments, neutral_comments = categorized_comments
        st.write("Number of Positive comments:", len(positive_comments))
        st.write("Number of Negative comments:", len(negative_comments))
        st.write("Number of Neutral comments:", len(neutral_comments))

        insert_sentiment_analysis(yturl, no_comment, len(positive_comments), len(negative_comments), len(neutral_comments))

    else:
        st.write("Please enter a valid YouTube URL.")

if st.button("Print Positive Comments"):
    if categorized_comments is not None:
        for comment in categorized_comments[0]:
            st.write("Positive:", comment)
    else:
        st.write("Please enter a valid YouTube URL.")

if st.button("Print Negative Comments"):
    if categorized_comments is not None:
        for comment in categorized_comments[1]:
            st.write("Negative:", comment)
    else:
        st.write("Please enter a valid YouTube URL.")

if st.button("Print Neutral Comments"):
    if categorized_comments is not None:
        for comment in categorized_comments[2]:
            st.write("Neutral:", comment)
    else:
        st.write("Please enter a valid YouTube URL.")
