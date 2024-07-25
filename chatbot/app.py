import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection URI
uri = "mongodb+srv://DbUser:TcZNUtefK0YavhiF@restaurantdb.ih0rfwo.mongodb.net/?retryWrites=true&w=majority&appName=RestaurantDb"

# Function to test MongoDB connection
def test_mongo_connection(uri):
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        return True
    except Exception as e:
        print(e)
        return False

# Streamlit UI
st.title("MongoDB Connection Test")

if st.button('Test MongoDB Connection'):
    with st.spinner("Connecting to MongoDB..."):
        if test_mongo_connection(uri):
            st.success("Pinged your deployment. You successfully connected to MongoDB!")
        else:
            st.error("Failed to connect to MongoDB. Please check your credentials and network.")
