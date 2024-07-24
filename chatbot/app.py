import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import textwrap
from IPython.display import Markdown
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Load environment variables
load_dotenv()  # take environment variables from .env.

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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
        page = reader.pages[page]
        text += str(page.extract_text())
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
    options = Options()
    options.add_argument('--headless')
    options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    driver = webdriver.Chrome(options=options)
    url = ""
    if site == "indeed":
        url = (
            URLS[site]
            + f"/jobs?q={skill_name.replace(' ', '+')}&l={location}&start={num_page * 10}"
        )
    driver.get(url)
    time.sleep(5)  # Let the page load (adjust this time according to your needs)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()  # Close the WebDriver after extracting the HTML
    return soup

def extract_job_description_and_company(driver, job_link):
    driver.get(job_link)
    time.sleep(5)  # Let the page load
    job_soup = BeautifulSoup(driver.page_source, "html.parser")
    job_description_elem = job_soup.find("div", {"id": "jobDescriptionText"})
    job_description = job_description_elem.text.strip() if job_description_elem else "N/A"
    company_name_tag = job_soup.select_one('[data-testid="inlineHeader-companyName"] span a')
    company_name = company_name_tag.text if company_name_tag else "N/A"
    driver.quit()
    return job_description, company_name

def scrape_jobs(skill_name, location, num_pages=1):
    job_data = []
    # MongoDB connection details (Replace <password> with your actual password)
    client = MongoClient(os.getenv('MONGO_URI'))
    db = client['job_database']
    collection = db['jobs']
    collection.create_index([('Job ID', 1)], unique=True)
    for page in range(num_pages):
        soup = extract_site(site="indeed", skill_name=skill_name, location=location, num_page=page)
        job_cards_div = soup.find("div", attrs={"id": "mosaic-provider-jobcards"})
        if job_cards_div:
            jobs = job_cards_div.find_all("li", class_="css-5lfssm eu4oa1w0")
            for job in jobs:
                job_link_elem = job.find('a')
                if job_link_elem:
                    job_id = job_link_elem.get('data-jk')
                    if not job_id:
                        continue
                    job_title_elem = job.find("h2", class_="jobTitle")
                    job_title = job_title_elem.text.strip() if job_title_elem else "N/A"
                    job_location_elem = job.find("div", class_="companyLocation")
                    job_location = job_location_elem.text.strip() if job_location_elem else "N/A"
                    job_link = f"https://ie.indeed.com/viewjob?jk={job_id}"
                    options = Options()
                    options.add_argument('--headless')
                    options.add_argument(f"user-agent={HEADERS['User-Agent']}")
                    driver = webdriver.Chrome(options=options)
                    job_description, company_name = extract_job_description_and_company(driver, job_link)
                    job_data.append({
                        'Job ID': job_id,
                        'Job Title': job_title,
                        'Company': company_name,
                        'Description': job_description,
                        'Link': job_link
                    })
        else:
            print("No job cards found on this page.")
    if job_data:
        try:
            collection.insert_many(job_data, ordered=False)
        except DuplicateKeyError as e:
            print(f"Duplicate data found in MongoDB: {e}")
    return job_data

# Streamlit UI
st.set_page_config(
    page_title="Q&A Demo and ATS Resume Expert",
    page_icon="🌟",
    layout="centered",
    initial_sidebar_state="auto"
)

st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Conversational AI for Tailored Educational Pathways</h1>", unsafe_allow_html=True)

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
                    st.subheader("The response is")
                    st.write(response)
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
   - Developed with best practices in explainable AI to ensure transparency and trust.
   - Provides clear explanations for its recommendations, allowingTo connect your Streamlit application to a MongoDB Atlas server, you need to ensure that you securely manage your MongoDB credentials and correctly set up the connection string. Here’s the modified section of your code that establishes the MongoDB connection using the `pymongo` library and incorporates best practices for handling sensitive information:

### Code Modifications

```python
from pymongo import MongoClient, errors

# MongoDB connection details
# Replace '<password>' with your actual MongoDB Atlas password and <dbname> with your database name.
# Ensure the connection URI is securely stored and not hard-coded in your script.
mongo_uri = os.getenv('MONGO_URI')  # Ensure this environment variable is set correctly

# Function to connect to MongoDB
def connect_to_mongo(uri):
    try:
        client = MongoClient(uri)
        db = client.get_database()  # Get the default database from the URI
        return db
    except errors.ConnectionError as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

# Connect to MongoDB Atlas
db = connect_to_mongo(mongo_uri)
if db:
    collection = db['jobs']
    collection.create_index([('Job ID', 1)], unique=True)

# The rest of your code continues here...

def scrape_jobs(skill_name, location, num_pages=1):
    job_data = []
    if not db:
        st.error("Database connection failed. Please check your MongoDB URI.")
        return job_data

    for page in range(num_pages):
        soup = extract_site(site="indeed", skill_name=skill_name, location=location, num_page=page)
        job_cards_div = soup.find("div", attrs={"id": "mosaic-provider-jobcards"})
        if job_cards_div:
            jobs = job_cards_div.find_all("li", class_="css-5lfssm eu4oa1w0")
            for job in jobs:
                job_link_elem = job.find('a')
                if job_link_elem:
                    job_id = job_link_elem.get('data-jk')
                    if not job_id:
                        continue
                    job_title_elem = job.find("h2", class_="jobTitle")
                    job_title = job_title_elem.text.strip() if job_title_elem else "N/A"
                    job_location_elem = job.find("div", class_="companyLocation")
                    job_location = job_location_elem.text.strip() if job_location_elem else "N/A"
                    job_link = f"https://ie.indeed.com/viewjob?jk={job_id}"
                    options = Options()
                    options.add_argument('--headless')
                    options.add_argument(f"user-agent={HEADERS['User-Agent']}")
                    driver = webdriver.Chrome(options=options)
                    job_description, company_name = extract_job_description_and_company(driver, job_link)
                    job_data.append({
                        'Job ID': job_id,
                        'Job Title': job_title,
                        'Company': company_name,
                        'Description': job_description,
                        'Link': job_link
                    })
        else:
            print("No job cards found on this page.")
    
    if job_data and db:
        try:
            collection.insert_many(job_data, ordered=False)
        except errors.BulkWriteError as e:
            print(f"Error inserting data into MongoDB: {e}")
    return job_data

# The Streamlit UI and other functions continue as before...
