import streamlit as st
from youtube_search import YoutubeSearch
from bs4 import BeautifulSoup
import re
import requests
import mysql.connector

# Function to connect to MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="yt_tags"
    )

# Function to insert title and tags into MySQL database
def insert_to_database(title, tag):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Concatenate all tag into a single string
        tag_str = ", ".join(tag)

        # Insert title and tag into the database
        sql = "INSERT INTO youtube_tag (title, tag) VALUES (%s, %s)"
        val = (title, tag_str)
        cursor.execute(sql, val)

        conn.commit()
        st.success("Data inserted into the database successfully.")

    except mysql.connector.Error as e:
        st.error(f"Error inserting data into the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Function to fetch tag from the YouTube video page
def fetch_tag(video_url):
    response = requests.get(video_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tag_elements = soup.find_all('meta', attrs={'property': 'og:video:tag'})
        tag = [tag['content'] for tag in tag_elements]
        return tag
    else:
        st.error("Failed to fetch tag from the video page.")
        return []

# Function to search for similar titles on YouTube
def search_similar_titles(title):
    results = YoutubeSearch(title, max_results=5).to_dict()
    tag_list = []

    for result in results:
        video_url = result['url_suffix']
        tag = fetch_tag("https://www.youtube.com" + video_url)
        tag_list.extend(tag)

    # Display tag side by side with less spacing
    tag_style = "background-color: #1abc9c; color: white; padding: 5px; border-radius: 5px; margin: 5px;"
    tag_html = "".join([f"<span style='{tag_style}'>{tag}</span>" for tag in tag_list])
    st.markdown(f"<div style='display: flex; flex-wrap: wrap;'>{tag_html}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Insert title and tag into database
    insert_to_database(title, tag_list)

# Streamlit app
def main():
    st.title("YouTube Tag Extractor")

    # Input field to enter the title
    search_title = st.text_input("Enter a title:")

    if st.button("Search"):
        if search_title:
            st.markdown("<p style='font-size: 18px; text-align: center;'>Tags from Similar Videos:</p>", unsafe_allow_html=True)
            search_similar_titles(search_title)
        else:
            st.warning("Please enter a title.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
