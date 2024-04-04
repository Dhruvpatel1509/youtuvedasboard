import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import mysql.connector
import base64

# Connect to MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="",  
        database="scheduler"  
    )

def suggest_next_publish_date(video_data):
    video_data['published_date'] = pd.to_datetime(video_data['published_date'])
    df_sorted = video_data.sort_values(by='published_date', ascending=False)
    average_diff = (df_sorted['published_date'] - df_sorted['published_date'].shift(-1)).mean()
    return df_sorted['published_date'].iloc[0] + average_diff

def insert_video_to_database(title, description, schedule_date, schedule_time):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        sql = "INSERT INTO scheduled_videos (title, description, schedule_date, schedule_time) VALUES (%s, %s, %s, %s)"
        val = (title, description, schedule_date, schedule_time)
        cursor.execute(sql, val)

        conn.commit()
        st.success("Video scheduled and saved to the database successfully.")

    except mysql.connector.Error as e:
        st.error(f"Error inserting video into the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
           
video_data = pd.read_excel('all_video_Data.xlsx')  
suggested_date = suggest_next_publish_date(video_data)

st.markdown(f"""
<style>
    .suggested-date {{
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        font-size: 20px;
        text-align: center;
    }}
</style>
<div class="suggested-date">Suggested next publishing time: {suggested_date.strftime('%H:%M:%S')}</div>
""", unsafe_allow_html=True)


video_title = st.text_input("Video Title")
video_description = st.text_area("Video Description")
schedule_date = st.date_input("Schedule Date", datetime.today())  
schedule_time = st.time_input("Schedule Time")

if st.button("Schedule Video"):

    insert_video_to_database(video_title, video_description, schedule_date, schedule_time)

# Display scheduled posts
st.subheader("Scheduled Videos")
try:
    conn = connect_to_database()
    df = pd.read_sql("SELECT * FROM scheduled_videos", conn)
    conn.close()

    df['schedule_time'] = df['schedule_time'].astype(str)

    st.table(df)
except Exception as e:
    st.error("Error fetching scheduled videos from the database.")  

csv = df.to_csv(index=False)
b64 = base64.b64encode(csv.encode()).decode() 
csv_link = f'<a href="data:file/csv;base64,{b64}" download="scheduled_videos.csv">Download CSV File</a>'
st.markdown(csv_link, unsafe_allow_html=True)
