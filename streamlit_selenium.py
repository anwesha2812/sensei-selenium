import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Replace 'YOUR_API_KEY' with your actual API key
api_key = "AIzaSyCk5y59_XIlabK3bDipO7FdPSD7lBguxIA"


# URL of your Google Apps Script web app
apps_script_url =  'https://script.google.com/macros/s/AKfycbyH2Dma-c3MLo2QnxKqnSRgbInX6nC48vS23PL4h7HuLoCfDSApaF4LzH6kWnctphY/exec'

def get_video_title(api_key, video_id):
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": api_key
    }

    response = requests.get(base_url, params=params)
    video_data = response.json()

    try:
        video_title = video_data["items"][0]["snippet"]["title"]
        return str(video_title)
    except (KeyError, IndexError):
        return None
    
def get_video_id(url):
    regex = r"(?<=watch\?v=)([\w-]+)"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    else:
        return None
    
def remove_non_alphabetic(input_string):
    # Use regular expression to remove non-alphabetic characters
    cleaned_string = re.sub(r'[^a-zA-Z0-9\s]', '', input_string)
    return cleaned_string

def remove_stopwords(sentence):
    stop_words = set(stopwords.words('english'))
    words = sentence.split()
    filtered_words = [word for word in words if word.lower() not in stop_words]
    return ' '.join(filtered_words)

# transcription 
def generate_transcription(video_id):
    # Get transcript
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    # Extract text from the transcript
    text = ''
    for entry in transcript:
        text += entry['text'] + ' '

    return text

def generate_pdf(text, output_file):
    # Create a PDF document
    c = canvas.Canvas(output_file, pagesize=letter)
    
    # Set font and size
    c.setFont("Helvetica", 12)

    # Split text into smaller chunks to fit in the PDF
    max_chars_per_line = 80
    lines = [text[i:i+max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
    
    # Add text to PDF
    y_position = 750
    for line in lines:
        c.drawString(50, y_position, line)  # Adjust position as needed
        y_position -= 15  # Adjust vertical position for the next line
    
    # Save the PDF
    c.save()
# transcription


def get_course_info(subject):
    # Set up ChromeOptions for headless mode
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Set the headless option
    options.add_argument('--disable-extensions')  # Disable extensions, including external scripts

    # Set up the ChromeDriver service with executable_path
    with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options) as driver:
        # Load the Coursera search URL
        driver.get(f'https://www.coursera.org/search?query={subject}')

        # Wait for the page to load (you might need to adjust the time based on your internet speed)
        driver.implicitly_wait(5)

        # Find all course elements using corrected XPath
        course_elements = driver.find_elements(By.CLASS_NAME, "cds-9.css-0.cds-11.cds-grid-item.cds-56.cds-64.cds-76")

        # Extract course information for the top 5 courses
        course_info = [
            {
                'title': title.find_element(By.CLASS_NAME, "cds-119.cds-CommonCard-title.css-e7lgfl.cds-121").text.strip(),
                'link': title.find_element(By.CLASS_NAME, "cds-119.cds-113.cds-115.cds-CommonCard-titleLink.css-si869u.cds-142").get_attribute('href'),
                'image': title.find_element(By.CLASS_NAME, "cds-9.css-0.cds-11.cds-grid-item.cds-56.cds-64.cds-76 img").get_attribute('src')
            }
            for title in course_elements[:5]
        ]

    return course_info


# Define the Streamlit app
def main():
    # Set title of the browser tab
    st.set_page_config(page_title="Sensei Extension")

    # Set the title of the Streamlit app
    st.title("Sensei Extension")   
    # Get query parameters
    youtube_url = st.experimental_get_query_params().get("youtube_url", [""])[0]

    if youtube_url:
        # st.write(f"Embedding YouTube video from URL: {youtube_url}")

        # Use st.video to embed the YouTube video
        st.video(youtube_url)
         # print(youtube_url)
        video_id = get_video_id(youtube_url)

        output_file = "output.pdf"  # Output PDF file name

        # Generate transcription
        transcription = generate_transcription(video_id)

        # Generate PDF
        generate_pdf(transcription, output_file)
        
        # print(video_id)
        # Get the YouTube video URL from the URL parameters
    

        user_input = remove_non_alphabetic(str(get_video_title(api_key,video_id)))
        sentence = user_input
        user_input = remove_stopwords(sentence)
        print(user_input)
        # Check if a YouTube URL is provided


        st.write("Recommended videos on the topic:")
        search_term =  user_input
        params = {"q": search_term}
        response = requests.get(apps_script_url, params=params)
    
        if response.status_code == 200:
            try:
                
                data = response.json()
                print(data)
                videos = data["videos"]

                # print("=======================")
                # print(videos)
                # print("=======================")
                
                top_videos = videos[:5]  # Get the top 5 videos with the highest view counts

                # Display the top videos in a row
                st.header("Top 5 Videos with the Highest View Counts", anchor='center')  # Anchor the header to the center

                for i, video in enumerate(top_videos):
                    # Create a container for thumbnail, table, and title
                    st.markdown(
                        f"<div style='display: flex; align-items: center; margin: 10px;'>"
                        f"<a href='https://www.youtube.com/watch?v={video['videoId']}' target='_blank'>"
                        f"<img src='https://img.youtube.com/vi/{video['videoId']}/default.jpg' width='240' height='180'></a>"
                        f"<div style='margin-left: 10px;'>"
                        f"<h3 style='font-size: 18px;'>{video['videoTitle']}</h3>"  # Adjust the font size here
                        f"<table style='text-align: center; margin-top: 10px;'><tr><th>View Count</th><th>Like Count</th></tr><tr>"
                        f"<td>{int(video['statistics']['viewCount']):,}</td>"
                        f"<td>{int(video['statistics']['likeCount']):,}</td></tr></table></div></div>",
                        unsafe_allow_html=True
                    )
            except ValueError as e:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                pretty_html = soup.prettify()
                st.markdown(pretty_html, unsafe_allow_html=True)
                st.error(f"Error parsing JSON: {e}")
        else:
            st.error("Error fetching data from the YouTube API, Status code: {response.status_code}")
            # Send the input to the Google Apps Script using a GET request

        subject_to_search = st.text_input("Enter the subject:", "Enter your subject...")

        # Display a submit button
        submit_button = st.button("Submit")

        # Check if the submit button is clicked
        if submit_button:
            # Display courses with images and titles in separate columns using Streamlit
            st.title(f"Coursera {subject_to_search.capitalize()} Courses")

            # Check if the user has entered a subject
            if subject_to_search:
                course_info = get_course_info(subject_to_search)

                for info in course_info[:5]:
                    # Display each container with thumbnail in the left column and title in the right column
                    st.markdown(
                        f'<div class="row" style="margin: 10px; display: flex; align-items: center; justify-content: space-around;">'
                        f'   <div style="flex: 1;"><a href="{info["link"]}" target="_blank"><img src="{info["image"]}" alt="{info["title"]}" style="width: 120px; height: 120px;"></a></div>'
                        f'   <div style="flex: 2; text-align: justify; font-weight: bold; margin: 10px;"><a href="{info["link"]}" target="_blank">{info["title"]}</a></div>'
                        f'</div>', unsafe_allow_html=True
                    )

                st.write("---")
        else:
            st.warning("Please enter a subject to search for courses.")
    else:
        st.warning("No YouTube video URL provided.")

    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
if __name__ == "__main__":
    main()





