import streamlit as st
import mysql.connector
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd  

def insert_channel_id(channel_url, channel_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Insert channel URL and ID into the database
        sql = "INSERT INTO channel_ids (channel_url, channel_id) VALUES (%s, %s)"
        val = (channel_url, channel_id)
        cursor.execute(sql, val)

        conn.commit()
        st.success("Channel ID inserted into the database successfully.")

    except mysql.connector.Error as e:
        st.error(f"Error inserting channel ID into the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_channel_id(channel_url):
    # Fetch HTML content of the YouTube channel page
    response = requests.get(channel_url)
    if response.status_code != 200:
        st.error(f"Failed to fetch the page. Status Code: {response.status_code}")
        return None

    # Parse HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Search for the channel ID in the meta tags
    channel_id_tag = soup.find('meta', {'itemprop': 'channelId'})

    if channel_id_tag:
        return channel_id_tag['content'].strip()  # Strip leading and trailing whitespaces
    else:
        # If the meta tag is not found, try searching for the channel ID in the script tags
        script_tags = soup.find_all('script')
        for script_tag in script_tags:
            match = re.search(r'"externalId":"([^"]+)"', script_tag.text)
            if match:
                return match.group(1).strip()  # Strip leading and trailing whitespaces

    st.error("Channel ID not found in the page source code.")
    return None
# Connect to MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="",  
        database="youtube_channel_ids"
    )

# Function to fetch channel IDs from the database
def fetch_channel_ids():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Fetch channel URLs and IDs from the database
        cursor.execute("SELECT channel_url, channel_id FROM channel_ids")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]  # Extract column names from cursor description
        df = pd.DataFrame(rows, columns=columns)

        return df

    except mysql.connector.Error as e:
        st.error(f"Error fetching channel IDs from the database: {e}")
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def main():
    st.title("YouTube Channel ID Finder")
    st.write("Enter the URL of the YouTube channel below:")

    channel_url = st.text_input("YouTube Channel URL")

    if st.button("Get Channel ID"):
        if channel_url:
            channel_id = get_channel_id(channel_url)
            if channel_id:
                st.success(f"The channel ID is: {channel_id}")
                insert_channel_id(channel_url, channel_id)
            else:
                st.error("Failed to retrieve the channel ID.")
        else:
            st.warning("Please enter a valid YouTube channel URL.")

    # Display channel IDs from the database in a table
    st.subheader("Previous Channel ID's which were extracted ")
    channel_ids_df = fetch_channel_ids()
    if channel_ids_df is not None:
        st.table(channel_ids_df)

if __name__ == "__main__":
    main()
