import streamlit as st
from pymongo import MongoClient

# Streamlit UI for login
st.set_page_config(
    page_title="login page",
    page_icon="🏋️‍♂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["EMS"]
collection = db["user_info"]
trainers_col = db["trainer"]
trainees_col = db["trainee"]
groups_col = db["groups"]



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


# Function to handle login
def login(login_email, login_password):
    # Your authentication logic here
    if collection.find_one({"_id": login_email}) is None:
        st.error("User not found", icon="⚠️")
        return None  # User not found
    user_data = collection.find_one({"_id": login_email})
    if user_data["details"]["password"] != login_password:
        st.error("Incorrect password")        
        return None  # Incorrect password
    return login_email  # Return the email after successful login



# Main function to run login
def main():
    with st.form("login form", border=True):
        # Apply the custom CSS        
        
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-main-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)
        st.markdown('<h2 class="center-heading">LOGIN FORM</h2>', unsafe_allow_html=True)
        st.markdown('<br><br>', unsafe_allow_html=True) 

        # Enter user info
        login_email = st.text_input(":darkblack[**Email**]", placeholder="Enter email here....")
        login_password = st.text_input(":darkblack[**Password**]", type="password", placeholder="Enter password here....")

        st.session_state.login_status = 0
        
        if st.form_submit_button("**Login**", type="primary",  use_container_width=True):
            if login_email == '':
                st.error("Please enter email")
            if login_password == '':
                st.error("Please enter password")
            else:
                login_result = login(login_email, login_password)
                if login_result:
                    st.session_state.login_status = 1
                    st.session_state.user_email = login_result  # Save the email in session state
                    st.success("Login successful")
                    st.switch_page("pages/main.py")

        st.markdown('<br>', unsafe_allow_html=True) 
        col1, col2, col3 = st.columns(3)
        col1.write("***New User? Click below***")
        if col1.form_submit_button("**Register**", type="primary", use_container_width=True):
            st.switch_page("pages/register.py")

        col3.write("***Forgot Password? Click below***")
        if col3.form_submit_button("**Change Password**", type="primary", use_container_width=True):
            st.switch_page("pages/change_password.py")

if __name__ == "__main__":
    main()
