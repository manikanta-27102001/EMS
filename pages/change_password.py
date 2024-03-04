import streamlit as st
from pymongo import MongoClient
import datetime
import time
import smtplib
from email.mime.text import MIMEText
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


st.set_page_config(
    page_title="change password page",
    page_icon="🏋️‍♂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
        font-size: 20px;  # You can customize the font size
        border-radius: 10px;
    }
        
    </style>
    """

# Load SMTP credentials from environment variables
smtp_server = os.getenv('SMTP_SERVER')
smtp_port = os.getenv('SMTP_PORT')
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')


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
        st.success("Click on Verification Tab above to submit verification code")
        return verification_code

    except smtplib.SMTPAuthenticationError:
        st.error("Login failed. Please check your email")
        return None

    except Exception as e:
        st.error("Login failed. Please check your email")
        # st.write(f"An error occurred: {e}")
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

    
tab1, tab2 = st.tabs(["Change Password", "Verification"])

with tab1:    
    with st.form("password reset form"):
        
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-main-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)
        st.markdown('<h2 class="center-heading">RESET PASSWORD FORM</h2><br>', unsafe_allow_html=True)            
        
        email = st.text_input("Email", placeholder="Enter your Email Address here...")
        password = st.text_input("New Password ", type="password", placeholder="Enter your new password here...")
        password1 = st.text_input("Confirm Password", type="password", placeholder="Re-enter your new password here...")
        submitted = st.form_submit_button("***Submit***", use_container_width=True,  type="primary")
        
        if submitted:
            if email == '' or password == '' or password1 == '':
                st.error("Fill all details to continue")
                st.stop()
            else:
                if check_password_strength(password):
                    if password != password1:
                        st.error("Passwords don't match")
                        st.stop()
                    else:
                        if collection.find_one({"_id": email}) == None:
                            st.error("User not found")
                        else:
                            code = send_email(email)
                            if code!= None:
                                st.session_state.verification_code = code
                                st.session_state.email = email
                                st.session_state.password = password
                                # verify_email(code, email, password)
                                                   
                else:
                    st.error("Password should contain 1 uppercase, 1 lowercase, 1 digit, 1 special character and minimum 8 characters")
                    st.stop()
                    
with tab2:
    with st.form(key= "verification form"):
        
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-main-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)
        st.markdown('<h2 class="center-heading">VERIFICATION FORM</h2>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True) 
        otp = st.text_input("**OTP**", placeholder="Enter OTP sent to email...")
        if st.form_submit_button("***Submit OTP***", use_container_width=True, type="primary"):
            code = st.session_state.verification_code
            email = st.session_state.email
            password = st.session_state.password
                                    
            if otp == code:
                st.success("OTP matched")
                user_data = collection.find_one({"_id": email})
                if "details" in user_data:
                    # Update password directly in the "details" field
                    result = collection.update_one(
                        {"_id": email},
                        {"$set": {"details.password": password}}
                    )
        
                if result.modified_count > 0:                                   
                    st.success("Password updated successfully.")       
                    with st.spinner('Redirecting to login page....'):
                        time.sleep(2)
                    st.switch_page("login.py")
                else:
                    st.error("Password not updated. Retry again")
            else:
                st.error("OTP incorrect")
