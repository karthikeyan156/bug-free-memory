import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import textwrap
from IPython.display import Markdown
from bs4 import BeautifulSoup
import requests
import json
import urllib.parse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# MongoDB connection URI
MONGO_URI = "mongodb+srv://DbUser:TcZNUtefK0YavhiF@restaurantdb.ih0rfwo.mongodb.net/?retryWrites=true&w=majority&appName=RestaurantDb"

# Function to test MongoDB connection
def test_mongo_connection(uri):
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        return True
    except Exception as e:
        print(e)
        return False

# Function to convert text to Markdown format
def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

# Function to get response from Gemini model
def get_gemini_response(input, pdf_content=None, prompt=None):
    if pdf_content:
        model = genai.GenerativeModel('gemini-pro-vision')
        response = model.generate_content([input, pdf_content[0], prompt])
    else:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(input)
    return response.text

# Function to extract text from PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        text += reader.pages[page].extract_text()
    return text

# Prompt Template
input_prompt = """
Hey Act Like a skilled or very experienced ATS(Application Tracking System)
with a deep understanding of tech field, software engineering, data science, data analyst
and big data engineer. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide
best assistance for improving the resumes. Assign the percentage Matching based
on JD and
the missing keywords with high accuracy
resume:{text}
description:{jd}

I want the response in one single string having the structure
{{"JD Match":"%","MissingKeywords:[]","Profile Summary":""}}
"""

# Web scraping functions
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
URLS = {
    "indeed": "https://ie.indeed.com"
}

def extract_site(site: str, skill_name: str, location="Ireland", num_page=0) -> BeautifulSoup:
    url = f"{URLS[site]}/jobs?q={skill_name.replace(' ', '+')}&l={location}&start={num_page * 10}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
    else:
        soup = None
    return soup

def scrape_jobs(skill_name, location, num_pages=1):
    job_data = []
    for page in range(num_pages):
        soup = extract_site(site="indeed", skill_name=skill_name, location=location, num_page=page)
        if soup:
            job_cards_div = soup.find("div", attrs={"id": "mosaic-provider-jobcards"})
            if job_cards_div:
                jobs = job_cards_div.find_all("div", class_="job_seen_beacon")
                for job in jobs:
                    job_id = job.get('data-jk')
                    job_title_elem = job.find("h2", class_="jobTitle")
                    job_title = job_title_elem.text.strip() if job_title_elem else "N/A"
                    company_elem = job.find("span", class_="companyName")
                    company_name = company_elem.text.strip() if company_elem else "N/A"
                    job_description_elem = job.find("div", class_="job-snippet")
                    job_description = job_description_elem.text.strip() if job_description_elem else "N/A"
                    job_data.append({
                        'Job ID': job_id,
                        'Job Title': job_title,
                        'Company': company_name,
                        'Description': job_description,
                    })
            else:
                print("No job cards found on this page.")
        else:
            print(f"Failed to retrieve page {page}")
    return job_data

# Streamlit UI
st.set_page_config(
    page_title="Q&A Demo and ATS Resume Expert",
    page_icon="🌟",
    layout="centered",
    initial_sidebar_state="auto"
)

st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Conversational AI for Tailored Educational Pathways</h1>", unsafe_allow_html=True)

# MongoDB Connection Test UI
st.sidebar.title("MongoDB Connection Test")
if st.sidebar.button('Test MongoDB Connection'):
    with st.spinner("Connecting to MongoDB..."):
        if test_mongo_connection(MONGO_URI):
            st.sidebar.success("Successfully connected to MongoDB!")
        else:
            st.sidebar.error("Failed to connect to MongoDB. Please check your settings.")

tab1, tab2 = st.tabs(["Q&A Chatbot", "ATS Resume Expert"])

with tab1:
    st.markdown("<h3 style='color: #4CAF50;'>Ask your question:</h3>", unsafe_allow_html=True)
    input_text = st.text_input("", key="input", placeholder="Type your question here...", help="Enter the question you want to ask Gemini")
    submit = st.button("Ask the Question")

    if submit:
        with st.spinner("Generating response..."):
            response = get_gemini_response(input_text)
        st.markdown("<h2 style='color: #4CAF50;'>The Response:</h2>", unsafe_allow_html=True)
        st.success(response)

with tab2:
    st.markdown("<h3 style='color: #4CAF50;'>Enter your resume or profile:</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Your Resume (PDF)...", type=["pdf"], help="Please upload the PDF")
    scrape_skill = st.text_input("Skill for Job Scraping", key="skill", placeholder="Enter the skill for job scraping...", help="Enter the skill you want to search for jobs")
    scrape_location = st.text_input("Location for Job Scraping", key="scrape_location", placeholder="Enter the location for job scraping...", help="Enter the location for job search")

    if uploaded_file is not None:
        st.write("PDF Uploaded Successfully")

    submit = st.button("Submit")

    if submit:
        if uploaded_file is not None:
            text = input_pdf_text(uploaded_file)
            if scrape_skill and scrape_location:
                with st.spinner("Scraping job data..."):
                    job_data = scrape_jobs(skill_name=scrape_skill, location=scrape_location)
                    job_descriptions = "\n\n".join([job['Description'] for job in job_data])
                    response = get_gemini_response(input_prompt.format(text=text, jd=job_descriptions))
                    response_data = json.loads(response)
                    missing_keywords = response_data.get("MissingKeywords", [])

                    # Display response
                    st.subheader("The response is")
                    st.write(response)

                    # Display links to learning resources for missing skills
                    if missing_keywords:
                        st.subheader("To learn a missing skill")
                        for keyword in missing_keywords:
                            coursera_url = f"https://www.coursera.org/search?query={urllib.parse.quote_plus(keyword)}"
                            udemy_url = f"https://www.udemy.com/courses/search/?src=ukw&q={urllib.parse.quote_plus(keyword)}"
                            st.write(f"Coursera: [Courses for {keyword}]({coursera_url})")
                            st.write(f"Udemy: [Courses for {keyword}]({udemy_url})")
            else:
                st.write("Please enter the skill and location for job scraping")
        else:
            st.write("Please upload the resume")

st.sidebar.title("Project Overview")
st.sidebar.info("""
**Title:** Personalized Educational and Career Pathway AI Chatbot

**Key Features:**

1. **Personalized Recommendations:**
   - The AI chatbot will recommend courses and educational pathways based on individual academic and career aspirations.
   - It will craft bespoke educational trajectories tailored to each learner's background, experience, and career objectives.

2. **Skill Extraction and Job Recommendations:**
   - The bot will analyze resumes to extract current skills and suggest suitable job opportunities.
   - It will identify skill gaps and recommend additional skills needed to achieve targeted job roles.

3. **Explainable AI:**
   - Developed withbest practices in explainable AI to ensure transparency and trust. 
   - Provides clear explanations for its recommendations, allowing users to understand and evaluate their future career evolution and options.

4. **Data-Driven Insights:**
   - Trained on survey data, market trends, and stakeholder inputs.
   - Adaptable to gender considerations, present and future job market needs, and STEM/non-STEM profiles.

5. **Interactive and Adaptive:**
   - The chatbot will ask targeted questions to understand the user's background, expectations, and needs.
   - Adapts its recommendations based on the user's input, providing a tailored program for both students and professionals.

6. **Career Guidance:**
   - Guides users in choosing the appropriate educational structure depending on their expertise and career stage.
   - Helps professionals assess their current skill set and suggests improvements for career advancement.

""")

st.markdown("""
    <hr style="height:2px;border:none;color:#4CAF50;background-color:#4CAF50;" />
    <footer style="text-align: center;">
        <p>© 2024 Conversational AI for Tailored Educational Pathways. All rights reserved.</p>
    </footer>
""", unsafe_allow_html=True)
