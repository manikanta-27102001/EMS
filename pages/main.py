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
from streamlit_option_menu import option_menu
from bson.binary import Binary
import base64
from login import main as login_main
import random
import string
import pandas as pd

# Streamlit configuration
st.set_page_config(
    page_title="EXERCISE MONITORING SYSTEM",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="auto",
)


# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["EMS"]
collection = db["user_info"]
trainers_col = db["trainer"]
trainees_col = db["trainee"]
groups_col = db["groups"]


# Custom CSS
custom_css = """
<style>
    .center-heading {
            background-color: royalblue;
            color: black;
            padding: 10px;
            border: 2px solid white;
            text-align: center;
            color: black;
            margin-top: 2px;
            border-radius: 10px;
            
        } 
        .center-main-heading{
            background-color: gray;
            color: black;
            padding: 10px;
            border: 2px solid white;
            text-align: center;
            color: black;
            margin-top: 2px;
            border-radius: 10px;
        }
        
        .user-id{
            background-color: teal;
            color: black;
            padding: 10px;
            border: 2px solid white;
            text-align: center;
            color: black;
            margin-top: 2px;
            border-radius: 10px;
        }
        .mail-id{
            color: firebrick;
            text-align: center;
            border-radius: 10px;
            
        }
        
</style>
"""


def home():
    with st.container(border = True, height = 660):
            # Apply the custom CSS
            st.markdown(custom_css, unsafe_allow_html=True)
            st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)               
        
    print("Home")


def tasks():
    with st.container(border = True, height = 660):
            # Apply the custom CSS
            st.markdown(custom_css, unsafe_allow_html=True)
            st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)               
        
    print("Tasks")



def generate_random_id():
    # Generate 3 random digits
    digits = ''.join(random.choices(string.digits, k=4))
    
    # Generate 3 random alphabets
    alphabets = ''.join(random.choices(string.ascii_letters, k=4))
    
    # Generate 2 random characters (either digit or alphabet)
    others = ''.join(random.choices(string.ascii_letters + string.digits, k=2))
    
    # Shuffle all characters
    id_characters = list(digits + alphabets + others)
    random.shuffle(id_characters)
    
    # Convert the list of characters to a string
    return ''.join(id_characters)



def create_group(group_name):
    # Check if the group name already exists
    email = st.session_state.user_email
    details = trainers_col.find_one({"_id": email})
    groups = details["groups"]
    existing_groups = [value for value in groups.values()]
    if group_name in existing_groups:
        return 0
    group_id = generate_random_id()
    
    # Insert the group into the database
    status = groups_col.find_one({"_id": group_id})
    if status:
        group_id = generate_random_id()
    group_data = {"_id": group_id, "name" : group_name, "creator_id": st.session_state.user_email, "members": [], 
                  "created_on": datetime.datetime.now().strftime("%d-%b-%Y"), "assigned":{}, "history":{}}
    
    try:
        groups_col.insert_one(group_data)
    except Exception as e:
        return -1

    # Update the trainers collection to include the group
    try:
        update_result = trainers_col.update_one({"_id": st.session_state.user_email}, {"$set": {"groups."+group_id: group_name}})
        if update_result.modified_count > 0:
            return 1
        else:
            return -1
    except Exception as e:
        # If updating the trainer's groups fails, delete the group created
        groups_col.delete_one({"_id": group_id})
        return -1

           
def assign_task():
    if "user_email" in st.session_state:
        user_email = st.session_state.user_email
    user_details = trainers_col.find_one({"_id": user_email})
    exercises_list = user_details["exercises"]
    selected_exercises = {}
    exercise_counts = {}
    with st.form("exercise_form", clear_on_submit=True):
        mid = len(exercises_list) // 2
        exercises_list_1 = exercises_list[:mid]
        exercises_list_2 = exercises_list[mid:]
        col1, col2 = st.columns(2)
        for exercise_1, exercise_2 in zip(exercises_list_1, exercises_list_2):
        
            exercise_count_1 = col1.number_input(exercise_1, min_value=0, format="%d")
            exercise_counts[exercise_1] = exercise_count_1

            exercise_count_2 = col2.number_input(exercise_2, min_value=0, format="%d")
            exercise_counts[exercise_2] = exercise_count_2
        submit_button = st.form_submit_button("**Submit**", type = "primary", use_container_width=True)
    
    if submit_button:
    # Filter exercises with counts > 0
        selected_exercises = {k: v for k, v in exercise_counts.items() if v > 0}
        
        if not selected_exercises:
            st.error("Please select at least one exercise to proceed.")
        else:
            st.markdown('<h3>Task Details</h3>', unsafe_allow_html=True)
            data = [{"Exercise": exercise, "Count": count} for exercise, count in selected_exercises.items()]
            st.table(data)
            
            with st.spinner('Assigning task...'):
                    time.sleep(4)
                
            st.success("Task assigned successfully")   
            if st.button("**Assign another task**", type = "primary", use_container_width=True):
                st.rerun()
            
            
    

def groups():
    with st.container():
        
        # Apply the custom CSS
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)        
        st.markdown('<br>', unsafe_allow_html=True)       
        tab1, tab2, tab3 = st.tabs(["Assign Tasks", "Create Group", "Group Details"])
           
        with tab1:  
            col11, col12, col13 = st.columns([1,3,1])  
            with col12: 
                with st.container(border = True):    
                    st.markdown('<h2 class = "center-main-heading" >Select Group(s)</h2><br>', unsafe_allow_html=True)
                    # Input for group name
                    if "group" not in st.session_state:
                        st.session_state.group = None        
                    if "user_email" in st.session_state:
                        user_email = st.session_state.user_email

                    if "group" not in st.session_state:
                        st.session_state.group = None  
                    if "option" not in st.session_state:
                        st.session_state.option = None
                    if "options" not in st.session_state:
                        st.session_state.options = []
                        
                    st.session_state.group = st.radio("**Choose One**", ["Single", "Multiple"], horizontal = True, index = None)
                    if st.session_state.group:
                        groups_info = trainers_col.find_one({"_id": user_email})
                        groups_list = groups_info["groups"].values()


                        if st.session_state.group == "Single":
                            st.session_state.option = st.selectbox("**Select a group**", groups_list, index=None, placeholder="Choose a group from below...")
                        elif st.session_state.group == "Multiple":
                            st.session_state.options = st.multiselect("**Select multiple groups**", groups_list,  placeholder="Choose groups from below...")

                        st.markdown('<h4>Groups selected are : </h4>', unsafe_allow_html=True)
                        
                        # Handling the display of selected groups based on the choice of single or multiple
                        if st.session_state.group == "Single" and st.session_state.option:
                            with st.container():
                                st.write(st.session_state.option)
                                assign_task()
                        elif st.session_state.group == "Multiple" and st.session_state.options:
                            with st.container():
                                st.write(", ".join(st.session_state.options))
                                assign_task()        
                                
                            
                            
                    
        with tab2: 
            col11, col12, col13 = st.columns([1,3,1])
            with col12:
                with st.container(border = True):    
                    st.markdown('<h2 class = "center-main-heading" >Create Group</h2><br>', unsafe_allow_html=True)
                    # Input for group name
                    group_name = st.text_input("**Group Name**", placeholder="Enter Group Name here...")


                    # Button to create the group
                    if st.button("Submit", key = "create_group", type="primary",  use_container_width=True):
                        if group_name:
                            res = create_group(group_name)
                            if res<0:
                                st.error("Group creation failed. Retry again.")
                                time.sleep(2)
                                st.rerun()
                            elif res==0:
                                st.error(f"Group '{group_name}' already exists. Please try with another name.")
                                
                            else:
                                st.success("Group created successfully")
                                time.sleep(2)
                                st.rerun()
                        else:
                            st.warning("Please enter a group name.")
                        
        with tab3:
            email = st.session_state.user_email
            trainer_data = trainers_col.find_one({"_id" : email})
            ids = list(trainer_data["groups"].keys())
            names = list(trainer_data["groups"].values())

            # Create a DataFrame to display the data in tabular format
            df = pd.DataFrame({"Group Names": names, "Group ID": ids})
            
            st.table(df)            
    
    
    
    
def dashboard():
    with st.container(border = True, height = 660):
        # Apply the custom CSS
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)               
    
    print("Dashboard")


def request1():
    with st.container(border = True, height = 660):
        # Apply the custom CSS
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)               




def request2():
    with st.container(border = True, height = 660):
        # Apply the custom CSS
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)       
        
        with st.container(border= True):
            id_list = []
            # Iterate over the documents in the collection
            for doc in groups_col.find({}, {"_id": 1, "name": 1}):
                # Concatenate _id and name and append to the list
                id_list.append(f"{doc['_id']}-{doc['name']}")
            group_id = st.selectbox("Search here", id_list, index=None,  placeholder="Enter Group ID/Group Name")
            
            c11, c22 = st.columns(2)
            
            if c11.button("Request To Join",key = "request to join",  use_container_width = True, type = "primary"):
                if group_id != None:
                    group_id = group_id[:10]
                    details = groups_col.find_one({"_id": group_id})
                    creator_id = details["creator_id"]
                    details1 = trainers_col.find_one({"_id": creator_id})
                    email = st.session_state.user_email
                    details2 = collection.find_one({"_id": email})
                    f_name = details2["details"]["first_name"]
                    l_name = details2["details"]["last_name"]
                    name = f_name + " " +l_name
                    
                    result = trainees_col.find_one({"_id": email, f"requests.{group_id}": {"$exists": True}})
                    present = 0
                    if result:
                        status = result["requests"][group_id]["status"]
                        if status == 0:
                            present = 1
                            c11.error("You have already requested")
                        elif status == 1:
                            present = 1
                            c11.success("You are already a member") 
                        elif status == -1:
                            present = 0
                    if present == 0:
                    
                        update_result1 = trainers_col.update_one({"_id": creator_id}, {"$push": {f"requests.{email}.groups": {"id": group_id, "info": [name, 0]}}})
                        update_result2 = trainees_col.update_one({"_id": email},    {"$set": {f"requests.{group_id}": {"status": 0}}})

                    

                        # Check if the update was successful
                        if update_result1.modified_count > 0 and update_result2.modified_count > 0:
                            st.success("Request sent")
                        else:
                            st.error("Failed !!! Try again")
                else:
                    st.error("Please select a group")
                    
                                
            if c22.button("Delete Request", key="delete Request", use_container_width=True, type="primary"):
                if group_id is not None:
                    group_id = group_id[:10]  
                    email = st.session_state.user_email 
                    details = groups_col.find_one({"_id": group_id})
                    creator_id = details["creator_id"]
                    
                    result = trainees_col.find_one({"_id": email, f"requests.{group_id}": {"$exists": True}})
                    if result:
                            
                        # Deletion query for trainees_col
                        result1 = trainees_col.update_one(
                            {"_id": email},
                            {"$unset": {f"requests.{group_id}": ""}}
                        )

                        # Deletion query for trainers_col
                        result2 = trainers_col.update_one(
                            {"_id": creator_id},
                            {"$pull": {f"requests.{email}.groups": {"id": group_id}}}
                        )



                        if result1.modified_count > 0 and result2.modified_count > 0:
                            st.success("Request deleted successfully.")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Failed to delete request.")
                    else:
                        st.error("You have not requested yet!!!!")
                else:
                    st.error("Please select a group")
                    
                
                
        with st.container(border = True):
            tab1, tab2, tab3 = st.tabs(["Accepted", "Pending", "Denied"])
            accepted = []
            pending = []
            denied = []
            email = st.session_state.user_email
            doc = trainees_col.find_one({"_id": email})

            if doc:
                requests = doc.get("requests", {})
                for group_id, data in requests.items():
                    status = data.get("status")
                    if status == 1:
                        accepted.append(group_id)
                    elif status == 0:
                        pending.append(group_id)
                    elif status == -1:
                        denied.append(group_id)

                        
            with tab1:
                if not accepted:
                    st.write("No accepted requests found")
                else:
                    documents = groups_col.find({"_id": {"$in": accepted}})
                    id_name_pairs1 = {}

                    for doc in documents:
                        id_name_pairs1[doc["_id"]] = doc.get("name")
                    
                    for _id, name in id_name_pairs1.items():
                        with st.container(border=True):
                            c1, c2, c3, c4 = st.columns([1,4,1, 1])
                            c1.markdown(f'<h4 style="color: #000000; ">Group Name:</h4>', unsafe_allow_html=True)
                            c2.markdown(f'<h4 style="color: #0000FF; ">{name}</h4>', unsafe_allow_html=True)
                            c3.markdown(f'<h4 style="color: #000000";>Group ID:</h4>', unsafe_allow_html=True)
                            c4.markdown(f'<h4 style="color: #0000FF;">{_id}</h4>', unsafe_allow_html=True)
                
                
            with tab2:
                if not pending:
                    st.write("No pending requests found")
                else:
                    documents = groups_col.find({"_id": {"$in": pending}})
                    id_name_pairs2 = {}

                    for doc in documents:
                        id_name_pairs2[doc["_id"]] = doc.get("name")
                    
                    # Iterate over id_name_pairs2 dictionary
                    for id, name in id_name_pairs2.items():
                        with st.container(border=True):
                            c1, c2, c3, c4 = st.columns([1,4,1, 1])
                            c1.markdown('<h4 style="color: #000000; ">Group Name:</h4>', unsafe_allow_html=True)
                            c2.markdown(f'<h4 style="color: #0000FF; ">{name}</h4>', unsafe_allow_html=True)
                            c3.markdown('<h4 style="color: #000000;">Group ID:</h4>', unsafe_allow_html=True)
                            c4.markdown(f'<h4 style="color: #0000FF;">{id}</h4>', unsafe_allow_html=True)
                            
            
            with tab3:
                if not denied:
                    st.write("No denied requests found")
                else:
                    documents = groups_col.find({"_id": {"$in": denied}})
                    id_name_pairs3 = {}

                    for doc in documents:
                        id_name_pairs3[doc["_id"]] = doc.get("name")
                    
                    for _id, name in id_name_pairs3.items():
                        with st.container(border=True):
                            c1, c2, c3, c4 = st.columns([1,4,1, 1])
                            c1.markdown(f'<h4 style="color: #000000;">Group Name:</h4>', unsafe_allow_html=True)
                            c2.markdown(f'<h4 style="color: #0000FF; ">{name}</h4>', unsafe_allow_html=True)
                            c3.markdown(f'<h4 style="color: #000000";>Group ID:</h4>', unsafe_allow_html=True)
                            c4.markdown(f'<h4 style="color: #0000FF;">{_id}</h4>', unsafe_allow_html=True)
                            
                            
                            
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


def profile():
    with st.container(border = True, height = 660):
        # Apply the custom CSS
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)  
        st.markdown('<br>', unsafe_allow_html=True)
    
        if "user_email" in st.session_state:
            user_email = st.session_state.user_email
            user_details = collection.find_one({"_id" : user_email})
            first_name = user_details["details"]["first_name"]
            last_name = user_details["details"]["last_name"]
            password = user_details["details"]["password"]
            
            if "first_name" not in st.session_state:
                st.session_state["first_name"] = first_name
            
            if "last_name" not in st.session_state:
                st.session_state["last_name"] = last_name
                
            
            if "password" not in st.session_state:
                st.session_state["password"] = password
                    
        with st.container(border=True):
            
            col1, col2, col3 = st.columns(3)
            col1.markdown('<h3 class = "user-id" >Name</h3>', unsafe_allow_html=True)
            col1.markdown(f'<h5 class = "mail-id" >{first_name} {last_name}</h5>', unsafe_allow_html=True)
            
            col2.markdown('<h3 class = "user-id" >User ID</h3>', unsafe_allow_html=True)
            col2.markdown(f'<h5 class = "mail-id" >{user_email}</h5>', unsafe_allow_html=True)
            
            col3.markdown('<h3 class = "user-id" >Rating</h3>', unsafe_allow_html=True)
            col3.markdown(f'<h5 class = "mail-id" >8.5/10</h5>', unsafe_allow_html=True)
            
        with st.container():
            col1, col2 = st.columns([2,1])
            with col1.form(key="personal_details"):
                st.markdown('<h2 class = "center-main-heading" >Update Personal Details</h2>', unsafe_allow_html=True)
                st.markdown('<br>', unsafe_allow_html=True)
                col3, col4 = st.columns([2, 1])
                st.session_state.first_name = col3.text_input(":darkblack[**First Name**]", value=st.session_state.first_name)
                st.session_state.last_name = col4.text_input(":darkblack[**Last Name**]", value=st.session_state.last_name)
                st.session_state.password = st.text_input(":darkblack[**Password**]", type="password", value=st.session_state.password)
                # st.markdown('<br>', unsafe_allow_html=True)
                if st.form_submit_button("***Submit***", type="primary", use_container_width=True):
                    
                    if st.session_state.first_name == '' or st.session_state.last_name == '' or st.session_state.password == '':
                        st.warning("Enter all details to continue")
                        st.stop()
                    else:
                        if check_password_strength(password):
                            # Update the document in MongoDB
                            query = {"_id": user_email}  
                            update_query = {
                                "$set": {
                                    "details.first_name": st.session_state.first_name,
                                    "details.last_name": st.session_state.last_name,
                                    "details.password": st.session_state.password
                                }
                            }
                            result = collection.update_one(query, update_query)

                            if result.modified_count > 0:
                                st.success("Details updated successfully.")
                                
                                st.rerun()
                            else:
                                st.error("Details not updated")
                        else:
                            st.warning("Password should contain 1 uppercase, 1 lowercase, 1 digit, 1 special character and minimum 8 characters")      
                            
                            
            with col2.container(border=True, height = 350):
                st.write("photo")
        
                            
def logout():
    with st.container(border = True):
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)  
        st.markdown('<br>', unsafe_allow_html=True)
    
        c1, c2, c3 = st.columns(3)
        with c2:
            st.markdown('<h3> Are you sure to logout?</h3>', unsafe_allow_html = True)
            c11, c12 , c13, c14= st.columns(4)
            if c12.button("**Yes**", type = "primary", use_container_width= True):
                st.switch_page("login.py")
          
                            



def main_1():
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",  # required
            options=["Home", "Groups", "Dashboard", "Requests", "Profile", "Logout"],  # required
            icons=["house", "people-fill", "display-fill", "chat-left-fill", "person-circle", "box-arrow-right"],  # optional
            menu_icon="menu-button-wide-fill",  # optional
            default_index=0,  # optional
            styles={
                "container": {"padding": "0!important", "background-color": "#C3E3EB",
                              "display": "flex", "justify-content": "space-around", }, 
                "icon": {"color": "Indianred", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "9px",
                    "--hover-color": "#90EE90",
                    "font-weight": "bold",     
                },
                "nav-link-selected": {"background-color": "#061E45"},

            },
        )

    if selected == "Home":
        home()
    elif selected == "Groups":
        groups()
    elif selected == "Dashboard":
        dashboard()
    elif selected == "Requests":
        request1()
    elif selected == "Profile":
        profile()
    elif selected == "Logout":
        logout()


def main_2():
        
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",  # required
            options=["Home", "Tasks", "Dashboard", "Requests", "Profile", "Logout"],  # required
            icons=["house", "list-task", "display-fill", "chat-left-fill", "person-circle", "box-arrow-right"],  # optional
            menu_icon="menu-button-wide-fill",  # optional
            default_index=0,  # optional
            styles={
                "container": {"padding": "0!important", "background-color": "#C3E3EB",
                              "display": "flex", "justify-content": "space-around", }, 
                "icon": {"color": "Indianred", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "9px",
                    "--hover-color": "#90EE90",
                    "font-weight": "bold",     
                },
                "nav-link-selected": {"background-color": "#061E45"},

            },
        )

    if selected == "Home":
        home()
    elif selected == "Tasks":
        tasks()
    elif selected == "Dashboard":
        dashboard()
    elif selected == "Requests":
        request2()
    elif selected == "Profile":
        profile()
    elif selected == "Logout":
        logout()
        
        
def main():
    if "user_email" in st.session_state:
        user_email = st.session_state.user_email
        user_details = collection.find_one({"_id" : user_email})
        role = user_details["role"]
        if role == "Trainer":
            main_1()
        else:
            main_2()
    
    
if __name__ == "__main__":
    st.session_state.local_status = False
    st.session_state.status = False
    if "login_status" in st.session_state:
        st.session_state.status = st.session_state["login_status"]
        if st.session_state.status:
            st.session_state.local_status = True
    if st.session_state.status or st.session_state.local_status:
        
        main()
        
    else:
        with st.container(border = True):
            # Apply the custom CSS
            st.markdown(custom_css, unsafe_allow_html=True)
            st.markdown('<h1 class="center-heading">EXERCISE MONITORING SYSTEM</h1>', unsafe_allow_html=True)    
            st.markdown('<br><br>', unsafe_allow_html=True)           
            col1, col2, col3 = st.columns(3)
                
            col2.error("You are not logged in. Please click below to login")
            if col2.button("**Login**", type = "primary"):
                st.switch_page("login.py")
                
                