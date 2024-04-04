import streamlit as st
import mysql.connector
from googleapiclient.discovery import build
import pandas as pd

# Function to connect to MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  
        database="score"  
    )

# Function to insert tag and score into MySQL database
def insert_to_database(tag, score):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Insert data into the database
        sql = "INSERT INTO tag_scores (tag, score) VALUES (%s, %s)"
        val = (tag, score)
        cursor.execute(sql, val)

        conn.commit()
        st.success("Data inserted into the database successfully.")

    except mysql.connector.Error as e:
        st.error(f"Error inserting data into the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Function to connect to YouTube Data API
def connect_to_youtube_api():
    API_KEY = "AIzaSyD3G6kUjq8KKalHZPbY1Ivh-rFyH2gyjuM"  
    return build('youtube', 'v3', developerKey=API_KEY)

# Function to normalize a value to a specific range
def normalize(value, min_val, max_val, new_min, new_max):
    return ((value - min_val) / (max_val - min_val)) * (new_max - new_min) + new_min

# Function to search for videos based on a tag and calculate a score
def analyze_tag(tag):
    youtube = connect_to_youtube_api()
    request = youtube.search().list(
        q=tag,
        part='snippet',
        type='video',
        maxResults=10
    )
    response = request.execute()

    total_score = 0
    max_score = 0

    for item in response['items']:
        video_id = item['id']['videoId']
        video_info = youtube.videos().list(part='statistics', id=video_id).execute()

        if 'statistics' in video_info['items'][0]:
            view_count = int(video_info['items'][0]['statistics']['viewCount'])
            like_count = int(video_info['items'][0]['statistics'].get('likeCount', 0))
            dislike_count = int(video_info['items'][0]['statistics'].get('dislikeCount', 0))

            # Calculate score
            score = view_count + like_count - dislike_count
            total_score += score
            max_score = max(max_score, score)

    if max_score > 0:
        average_score = normalize(total_score, 0, max_score * 10, 1, 10)
        st.success(f"Average Score for tag '{tag}': {average_score:.2f}")
        
        # Insert tag and score into the database
        insert_to_database(tag, average_score)
    else:
        st.warning("No videos found for the given tag.")


def fetch_data_from_database():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Fetch data from the database
        cursor.execute("SELECT tag, score FROM tag_scores")
        data = cursor.fetchall()

        return data

    except mysql.connector.Error as e:
        st.error(f"Error fetching data from the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


            
def main():
    st.title("YouTube Keyword Analyzer")

    # Fetch data from the database
    data = fetch_data_from_database()

    
    # Input field to enter the tag
    tag = st.text_input("Enter a tag:")

    if st.button("Analyze"):
        if tag:
            # Analyze the tag
            analyze_tag(tag)
        else:
            st.warning("Please enter a tag.")
    # Display data in a table
    st.write("Data from the database:")
    if data:
        df = pd.DataFrame(data, columns=["Tag", "Score"])
        df.set_index("Tag", inplace=True)  
        st.dataframe(df)
    else:
        st.warning("No data found in the database.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
