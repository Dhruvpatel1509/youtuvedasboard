import streamlit as st
from youtube_search import YoutubeSearch
import re
import requests
from PIL import Image
from io import BytesIO
import mysql.connector

# Connect to MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="",  
        database="best_titles"  
    )

# Function to insert video data into MySQL database
def insert_video_data(title, thumbnail_url, view_count):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Insert data into the database
        sql = "INSERT INTO similar_videos (title, thumbnail_url, view_count) VALUES (%s, %s, %s)"
        val = (title, thumbnail_url, view_count)
        cursor.execute(sql, val)

        conn.commit()
        st.success("Video data inserted into the database successfully.")

    except mysql.connector.Error as e:
        st.error(f"Error inserting video data into the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Function to convert view count string to an integer
def extract_view_count(view_count):
    count = re.sub(r'[^\d.]', '', view_count)
    return int(float(count))

# Function to format view count as million or thousand
def format_view_count(view_count):
    if view_count >= 1e6:
        return f"{view_count/1e6:.1f}M"
    elif view_count >= 1e3:
        return f"{view_count/1e3:.1f}K"
    else:
        return str(view_count)

# Function to search for similar titles on YouTube
def search_similar_titles(title):
    results = YoutubeSearch(title, max_results=10).to_dict()

    sorted_results = sorted(results, key=lambda x: extract_view_count(x['views']), reverse=True)

    # Set the size and alignment for titles and views
    title_style = "font-size: 24px; text-align: center;"
    views_style = "font-size: 16px; text-align: center;"

    # Set the size for thumbnails and adjust the number of columns
    thumbnail_width = 400  # Increase the thumbnail width for higher quality

    num_columns = 2

    for i, result in enumerate(sorted_results):
        video_title = result['title']
        video_views = format_view_count(extract_view_count(result['views']))

        # Get the video ID
        video_id = result['id']

        # Construct the URL to retrieve the thumbnail image in higher quality
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        # Load and resize the thumbnail image
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            image.thumbnail((thumbnail_width, thumbnail_width))

            # Set the alignment and style for title and view count
            st.markdown(f"<h3 style='{title_style}'>{video_title}</h3>", unsafe_allow_html=True)
            st.image(image, use_column_width=True)
            st.markdown(f"<p style='{views_style}'>Views: {video_views}</p>", unsafe_allow_html=True)

            # Insert data into the database
            insert_video_data(video_title, thumbnail_url, extract_view_count(result['views']))

            # Insert a line break after every second video to create two columns
            if (i + 1) % num_columns == 0:
                st.write("---")

# Streamlit app
def main():
    st.title("YouTube Title Search")

    # Input field to enter the title
    search_title = st.text_input("Enter a title:")

    if st.button("Search"):
        if search_title:
            st.markdown("<p style='font-size: 24px; text-align: center;'>These are some videos similar to your title having plenty of views:</p>", unsafe_allow_html=True)
            st.write("---")
            # Call the function to search for similar titles
            search_similar_titles(search_title)
        else:
            st.warning("Please enter a title.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
