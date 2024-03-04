import streamlit as st
from pymongo import MongoClient
import datetime
import time
import smtplib
from email.mime.text import MIMEText
from pymongo.errors import DuplicateKeyError
import random
import string
import os
import re
import json
from dotenv import load_dotenv

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["EMS"]
collection = db["user_info"]
trainers_col = db["trainer"]
trainees_col = db["trainee"]
groups_col = db["groups"]


# Load variables from the .env file
load_dotenv()


# Load SMTP credentials from environment variables
smtp_server = os.getenv('SMTP_SERVER')
smtp_port = os.getenv('SMTP_PORT')
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')



st.set_page_config(
    page_title="registration page",
    page_icon="🏋️‍♂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# custom login
custom_css = """
<style>
    .center-heading {
            background-color: royalblue;
            color: black;
            padding: 10px;
            border: 2px solid white;
            text-align: center;
            border-radius: 10px;
        }
    
    .center-main-heading{
        text-align: center;
        color: black;  # You can customize the color
        font-size: 30px;  # You can customize the font size
        border-radius: 10px;
    }
</style>
"""



def send_email(email):
    # generating verification code
    verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    st.session_state.verification_code = verification_code

    # Prepare verification email
    msg = MIMEText(f'Your verification code is: {verification_code}')
    msg['Subject'] = 'Email Verification'
    msg['From'] = smtp_username
    msg['To'] = email

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

        # Send email
        server.sendmail(smtp_username, email, msg.as_string())
        st.success("Verification code sent to your email address.")
        return verification_code

    except smtplib.SMTPAuthenticationError:
        st.error("Login failed. Please check your email")
        return None

    except Exception as e:
        st.error("Login failed. Please check your email")
        return None

    finally:
        # Quit the server
        if 'server' in locals():
            server.quit()


# check password strength
def check_password_strength(password):
    # Length of password 
    if len(password)<8:
        return False
        
    # Check for at least one uppercase letter
    uppercase_regex = re.compile(r'[A-Z]')
    if not uppercase_regex.search(password):
        return False

    # Check for at least one lowercase letter
    lowercase_regex = re.compile(r'[a-z]')
    if not lowercase_regex.search(password):
        return False

    # Check for at least one digit
    digit_regex = re.compile(r'\d')
    if not digit_regex.search(password):
        return False

    # Check for at least one special character
    special_char_regex = re.compile(r'[!@#$%^&*(),.?":{}|<>]')
    if not special_char_regex.search(password):
        return False

    return True


# Function to verify code
def verify_email(verification_code, user_verification_code):
    
    if user_verification_code == verification_code:
        return True
    else:
        st.warning("OTP Incorrect")
        return False


 
tab1, tab2 = st.tabs(["Register", "Verification"])

# Main code
with tab1:
    with st.form("registration form", border = True):
        # Apply the custom CSS
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-main-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)
        st.markdown('<h2 class="center-heading">REGISTRATION FORM</h2>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True) 
        col1, col2 = st.columns([2, 1])
        f_name = col1.text_input(":darkblack[**First Name**]", placeholder="Enter here....")
        l_name = col2.text_input(":darkblack[**Last Name**]", placeholder="Enter here....")
        col3, col4 = st.columns([2,1])
        email= col3.text_input(":darkblack[**Email**]", placeholder="Enter email here....")
        role = col4.selectbox(':darkblack[**Role**]', ("Trainee", "Trainer"), index = None, placeholder="Select your role here....")
        col5, col6 = st.columns(2)
        gender = col5.selectbox(":darkblack[**Gender**]", ("MALE", "FEMALE", "OTHERS"), index=None, placeholder="Select your gender")
        dob = col6.date_input(":darkblack[**Select your date of birth**]", format="DD/MM/YYYY", value=None, min_value=datetime.date(1950, 1, 1), max_value=datetime.date.today())
        password = col5.text_input(":darkblack[**Password**]", type="password", placeholder="Enter password here....")
        password1 = col6.text_input(":darkblack[**Re-Enter Password**]", type="password", placeholder="Re-Enter password here....")

       # convert dob from date type object to datetime
        dob = datetime.datetime.combine(dob, datetime.datetime.min.time()) if dob else None

       
        # session state variables
        st.session_state.first_name = f_name
        st.session_state.last_name = l_name
        st.session_state.email = email
        st.session_state.role = role
        st.session_state.gender = gender
        st.session_state.dob = dob
        st.session_state.password = password
        
        
        if st.form_submit_button("***Register***", type="primary", use_container_width=True):
        
            if dob is None:
                st.error("Invalid date of birth.")
            else:
                if  email == '' or f_name == '' or l_name == '' or role == None or gender == None or dob == None or password == ''  or password1 == '':
                    st.warning("Enter all details to continue")
                    st.stop()
                else:
                    
                    if check_password_strength(password):
                                if password1 != password:
                                    st.warning("Passwords do not match")
                                    st.stop()
                                else:
                                    if collection.find_one({"_id": email}) != None:
                                        st.error("User already exists")
                                
                                    
                                    else:
                                        code = send_email(email)
                                        if code!= None:
                                            st.success("Click on :red[Verification] Tab above to submit verification code")
            
                    else:
                        st.warning("Password should contain 1 uppercase, 1 lowercase, 1 digit, 1 special character and minimum 8 characters")      
                        st.stop()
       
with tab2:
    with st.form("verification form", border= True):
        # Apply the custom CSS
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-main-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)
        st.markdown('<h2 class="center-heading">VERIFICATION FORM</h2>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True) 
        user_verification_code = st.text_input("**OTP**", placeholder="Enter OTP send to your mail")
        submitted = st.form_submit_button("Verify Code", type="primary",  use_container_width=True)
        if submitted:                
            # Get session state variables
            f_name = st.session_state.first_name 
            l_name = st.session_state.last_name 
            email = st.session_state.email 
            gender = st.session_state.gender
            role = st.session_state.role
            dob = st.session_state.dob 
            password = st.session_state.password 
            verification_code = st.session_state.verification_code
            
            
            if verify_email(verification_code, user_verification_code):
                # Store data in MongoDB
                user_data = {
                    "_id": email,
                    "role" : role,
                    "registered_on": datetime.datetime.now().strftime("%d-%b-%Y"),
                    "details":{
                    "first_name": f_name,
                    "last_name": l_name,
                    "gender": gender,
                    "DOB": dob,
                    "password": password}
                }
                
                # inserting data into user_info collection 
                result_1 = collection.insert_one(user_data)
                inserted_id_1 = result_1.inserted_id  # Get the _id of the inserted document
                
                
                if role == "Trainer":
                    # Define the data structure
                    trainer_data = {
                        "_id": email,
                        "groups": {},
                        "exercises": ["Curl", "Push-up", "Squat", "Jump"],
                        "requests" : {}
                    }
                    result_2 = trainers_col.insert_one(trainer_data)
                    inserted_id_2 = result_2.inserted_id  # Get the _id of the inserted document
                    
                    if inserted_id_1 != None and inserted_id_2 != None:
                        status = True
                    else:
                        if inserted_id_1:
                            if inserted_id_2 == None:
                                filter_criteria = {"_id": email}
                                collection.delete_one(filter_criteria)
                                
                            
                        if inserted_id_2:
                            if inserted_id_1 == None:
                                filter_criteria = {"_id": email}
                                trainers_col.delete_one(filter_criteria)
                                
                        st.error("Failed to register. Retry again.")
                        status = False
                        
                else:
                    trainee_data = {
                        "_id": email,
                        "groups": {},
                        "daily_info": {},
                        "requests" : {}
                    }
                    result_3 = trainees_col.insert_one(trainee_data)
                    inserted_id_3 = result_3.inserted_id  # Get the _id of the inserted document
                    
                    if inserted_id_1 and inserted_id_3:
                        status = True
                    else:
                        if inserted_id_1:
                            
                            if inserted_id_3 == None:
                                filter_criteria = {"_id": email}
                                collection.delete_one(filter_criteria)
                                
                            
                        if inserted_id_3:
                            if inserted_id_1 == None:
                                filter_criteria = {"_id": email}
                                trainees_col.delete_one(filter_criteria)
                                
                        st.error("Failed to register. Retry again.")
                        status = False
                    
                if status:
                    st.success("Registration successful!!!!")
                    st.balloons()
                    with st.spinner('Redirecting to login form...'):
                        time.sleep(4)
                    st.switch_page("login.py")
        

