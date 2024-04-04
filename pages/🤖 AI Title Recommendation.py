import streamlit as st
import replicate
import mysql.connector

# Connect to MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="",  
        database="ai_titles"  
    )

# Function to insert title input and recommendations text into MySQL database
def insert_recommendations(title, recommendations_text):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Insert data into the database
        sql = "INSERT INTO title_recommendations (title, recommendations_text) VALUES (%s, %s)"
        val = (title, recommendations_text)
        cursor.execute(sql, val)

        conn.commit()
        st.success("Data inserted into the database successfully.")

    except mysql.connector.Error as e:
        st.error(f"Error inserting data into the database: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def generate_recommendations(title):
    prompt = f"GIVE ME FIVE YT TITLE RECOMMENDATIONS FOR: {title} under 10 words for  each title"
    output = replicate.run(
        "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
        input={
            "prompt": prompt,
            "max_tokens": 1000
        }
    )

    recommendations_text = ""
    for item in output:
        recommendations_text += item

    return recommendations_text

def main():
    st.title("YouTube Title Recommendations")

    title = st.text_input("Enter a YouTube title:", "")
    st.write("Click the button below to get recommendations based on the entered title.")

    if st.button("Get Recommendations") and title.strip() != "":
        recommendations_text = generate_recommendations(title)
        st.write("Here are your recommendations:")
        st.write(recommendations_text)

        # Insert title and recommendations into database
        insert_recommendations(title, recommendations_text)

if __name__ == "__main__":
    main()
