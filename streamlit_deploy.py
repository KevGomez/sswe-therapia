#!/usr/bin/env python3
"""
Streamlit UI for the Therapist-Client Scheduling System - Deployment Version
This file is optimized for Streamlit Cloud deployment.
"""

import streamlit as st
import datetime
from datetime import timedelta
import json
import os
import sys
from typing import List, Dict, Any, Optional
import traceback

# Show version info in logs for debugging
st.write(f"Python version: {sys.version}")
st.write(f"Streamlit version: {st.__version__}")

# Directly check for secrets first before trying imports
if hasattr(st, 'secrets') and 'firebase' in st.secrets:
    st.write("Firebase secrets found in Streamlit config!")
    # Display keys that are present (but not their values)
    st.write(f"Firebase config keys available: {list(st.secrets.firebase.keys())}")
else:
    st.error("Firebase secrets NOT found in Streamlit config!")
    st.error("Please add Firebase credentials in the Streamlit Cloud dashboard under 'Secrets' section.")
    if hasattr(st, 'secrets'):
        st.write(f"Available secret sections: {list(st.secrets.keys())}")
    else:
        st.write("No secrets available at all.")

# Add error handling wrapper for the entire app
try:
    # Configure the page
    st.set_page_config(
        page_title="Therapist-Client Scheduling",
        page_icon="🗓️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Display a loading message while imports are happening
    with st.spinner("Loading application components..."):
        # Try importing the required modules
        try:
            # Import utility functions first
            from app.utils.date_utils import format_time_slot
            from app.schemas.time_slot import TimeSlotResponse
            
            # Create a simple TimeSlot implementation in case the imports fail
            # This avoids circular imports
            class TimeSlot:
                def __init__(self, start_time, end_time, status="free"):
                    self.start_time = start_time
                    self.end_time = end_time
                    self.status = status
            
            # Try to initialize Firebase directly here to debug any issues
            import firebase_admin
            from firebase_admin import credentials, db
            
            st.write("Successfully imported Firebase modules")
            
            # Function to get Firebase credentials
            def get_firebase_credentials():
                if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                    # Check if private key is available and properly formatted
                    if 'FIREBASE_PRIVATE_KEY' in st.secrets.firebase:
                        private_key = st.secrets.firebase.FIREBASE_PRIVATE_KEY
                        st.write(f"Private key found (length: {len(private_key)})")
                        # Check for proper formatting
                        if not (private_key.startswith("-----BEGIN PRIVATE KEY-----") and 
                               private_key.endswith("-----END PRIVATE KEY-----\n")):
                            st.warning("Private key doesn't have the expected format!")
                    else:
                        st.error("FIREBASE_PRIVATE_KEY not found in secrets!")
                        
                    return {
                        "type": "service_account",
                        "project_id": "sansa-sswe-kevin",
                        "private_key_id": st.secrets.firebase.get("FIREBASE_PRIVATE_KEY_ID", ""),
                        "private_key": st.secrets.firebase.get("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
                        "client_email": st.secrets.firebase.get("FIREBASE_CLIENT_EMAIL", ""),
                        "client_id": st.secrets.firebase.get("FIREBASE_CLIENT_ID", ""),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": st.secrets.firebase.get("FIREBASE_CLIENT_CERT_URL", "")
                    }
                # Fall back to environment variables
                else:
                    st.warning("Using environment variables instead of Streamlit secrets")
                    return {
                        "type": "service_account",
                        "project_id": "sansa-sswe-kevin",
                        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
                        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
                        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
                        "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", "")
                    }
            
            # Initialize Firebase
            try:
                cred_data = get_firebase_credentials()
                # Check for any empty required fields
                empty_fields = [k for k, v in cred_data.items() if not v and k in [
                    "private_key_id", "private_key", "client_email", "client_id", "client_x509_cert_url"
                ]]
                
                if empty_fields:
                    st.error(f"Missing required Firebase credential fields: {empty_fields}")
                
                # Initialize Firebase only if no apps are already initialized
                if not firebase_admin._apps:
                    cred = credentials.Certificate(cred_data)
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': 'https://sansa-sswe-kevin-default-rtdb.firebaseio.com/'
                    })
                    st.success("Firebase initialized successfully!")
                else:
                    st.success("Firebase already initialized")
                
                # Reference to database
                db_ref = db.reference('appointments')
                
                # Define simple wrapper functions to test database access
                def create_free_slot(therapist_id, start_time, end_time):
                    try:
                        st.write(f"Creating slot for {therapist_id}: {start_time} to {end_time}")
                        # Simplified version for testing
                        therapist_ref = db_ref.child(therapist_id)
                        slots_data = therapist_ref.get() or []
                        
                        # Create new slot
                        new_slot = {
                            "start_time": start_time.isoformat(),
                            "end_time": end_time.isoformat(),
                            "status": "free"
                        }
                        slots_data.append(new_slot)
                        
                        # Save updated slots
                        therapist_ref.set(slots_data)
                        return True
                    except Exception as e:
                        st.error(f"Error creating slot: {str(e)}")
                        st.error(traceback.format_exc())
                        return False
                
                def list_available_slots(therapist_id, search_date):
                    try:
                        st.write(f"Listing slots for {therapist_id} on {search_date}")
                        therapist_ref = db_ref.child(therapist_id)
                        slots_data = therapist_ref.get() or []
                        
                        # Filter slots by date and status
                        available_slots = []
                        for slot_dict in slots_data:
                            slot_start = datetime.datetime.fromisoformat(slot_dict["start_time"])
                            slot_end = datetime.datetime.fromisoformat(slot_dict["end_time"])
                            slot_date = slot_start.date()
                            
                            if slot_date == search_date and slot_dict["status"] == "free":
                                available_slots.append(TimeSlot(
                                    start_time=slot_start,
                                    end_time=slot_end,
                                    status=slot_dict["status"]
                                ))
                        
                        return available_slots
                    except Exception as e:
                        st.error(f"Error listing slots: {str(e)}")
                        st.error(traceback.format_exc())
                        return []
                
                def book_slot(therapist_id, slot_time):
                    try:
                        st.write(f"Booking slot for {therapist_id} at {slot_time}")
                        therapist_ref = db_ref.child(therapist_id)
                        slots_data = therapist_ref.get() or []
                        
                        # Find and update the slot
                        for i, slot_dict in enumerate(slots_data):
                            slot_start = datetime.datetime.fromisoformat(slot_dict["start_time"])
                            
                            # Check if this is the slot we want to book
                            if slot_start == slot_time:
                                # Check if slot is already booked
                                if slot_dict["status"] == "busy":
                                    return False
                                
                                # Update slot status to busy
                                slots_data[i]["status"] = "busy"
                                therapist_ref.set(slots_data)
                                return True
                        
                        return False  # Slot not found
                    except Exception as e:
                        st.error(f"Error booking slot: {str(e)}")
                        st.error(traceback.format_exc())
                        return False
                
                def cancel_booking(therapist_id, slot_time):
                    try:
                        st.write(f"Canceling booking for {therapist_id} at {slot_time}")
                        therapist_ref = db_ref.child(therapist_id)
                        slots_data = therapist_ref.get() or []
                        
                        # Find and update the slot
                        for i, slot_dict in enumerate(slots_data):
                            slot_start = datetime.datetime.fromisoformat(slot_dict["start_time"])
                            
                            # Check if this is the slot we want to cancel
                            if slot_start == slot_time:
                                # Check if slot is actually booked
                                if slot_dict["status"] == "free":
                                    return False
                                
                                # Update slot status to free
                                slots_data[i]["status"] = "free"
                                therapist_ref.set(slots_data)
                                return True
                        
                        return False  # Slot not found
                    except Exception as e:
                        st.error(f"Error canceling booking: {str(e)}")
                        st.error(traceback.format_exc())
                        return False
                
            except Exception as e:
                st.error(f"Firebase initialization error: {str(e)}")
                st.error(traceback.format_exc())
                
                # Create dummy functions that show errors when used
                def create_free_slot(therapist_id, start_time, end_time):
                    st.error("Firebase not initialized - cannot create slots")
                    return False
                
                def list_available_slots(therapist_id, search_date):
                    st.error("Firebase not initialized - cannot list slots")
                    return []
                
                def book_slot(therapist_id, slot_time):
                    st.error("Firebase not initialized - cannot book slots")
                    return False
                
                def cancel_booking(therapist_id, slot_time):
                    st.error("Firebase not initialized - cannot cancel bookings")
                    return False
            
            # Remove debug info once everything is loaded
            if not st.session_state.get('debug_mode', False):
                st.empty()
            
            # Session state initialization
            if 'therapist_id' not in st.session_state:
                st.session_state['therapist_id'] = ''
            if 'user_role' not in st.session_state:
                st.session_state['user_role'] = None
            if 'debug_mode' not in st.session_state:
                st.session_state['debug_mode'] = True  # Set to True for debugging
                
            # Custom styling
            st.markdown("""
            <style>
                .main {
                    background-color: #f8f9fa;
                }
                .stApp {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .appointment-card {
                    background-color: #ffffff;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px 0;
                    border-left: 5px solid #4CAF50;
                }
                .stTabs [data-baseweb="tab-list"] {
                    gap: 24px;
                }
                .stTabs [data-baseweb="tab"] {
                    height: 50px;
                    white-space: pre-wrap;
                    background-color: #f0f2f6;
                    border-radius: 4px 4px 0 0;
                    gap: 1px;
                    padding-top: 10px;
                    padding-bottom: 10px;
                }
                .stTabs [aria-selected="true"] {
                    background-color: #4CAF50 !important;
                    color: white !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            def main():
                """Main Streamlit app function"""
                
                # Debug toggle for development
                if st.sidebar.checkbox("Debug Mode", value=st.session_state.get('debug_mode', True)):
                    st.session_state['debug_mode'] = True
                else:
                    st.session_state['debug_mode'] = False
                    # Clear previous debug messages
                    st.empty()
                
                # Sidebar for user selection
                with st.sidebar:
                    st.title("🗓️ Scheduling App")
                    st.markdown("---")
                    
                    # User role selection
                    st.header("Select Your Role")
                    role_options = ["Therapist", "Client"]
                    
                    if st.session_state['user_role'] is None:
                        selected_role = st.selectbox("I am a:", role_options)
                        if st.button("Continue"):
                            st.session_state['user_role'] = selected_role
                            st.rerun()
                    else:
                        st.info(f"Current role: {st.session_state['user_role']}")
                        
                        # User ID input
                        st.session_state['therapist_id'] = st.text_input(
                            "Enter your ID:",
                            value=st.session_state['therapist_id']
                        )
                        
                        if st.button("Change Role"):
                            st.session_state['user_role'] = None
                            st.rerun()
                            
                # Main content area
                if st.session_state['user_role'] is None:
                    show_welcome_page()
                elif not st.session_state['therapist_id']:
                    st.warning("Please enter your ID in the sidebar to continue.")
                elif st.session_state['user_role'] == "Therapist":
                    show_therapist_dashboard()
                elif st.session_state['user_role'] == "Client":
                    show_client_dashboard()


            def show_welcome_page():
                """Display welcome page"""
                st.title("Welcome to the Therapist-Client Scheduling System")
                
                st.markdown("""
                This application helps therapists and clients schedule appointments efficiently.
                
                ### Features:
                - **For Therapists**: Create and manage available time slots
                - **For Clients**: View available slots and book appointments
                - **For Both**: Manage existing bookings
                
                Please select your role from the sidebar to get started.
                """)
                
                # Display sample screenshots or instructions
                with st.expander("How to use this app"):
                    st.markdown("""
                    1. Select your role (Therapist or Client) from the sidebar
                    2. Enter your unique identifier
                    3. Use the dashboard to manage your schedule or bookings
                    """)


            def show_therapist_dashboard():
                """Display therapist dashboard"""
                therapist_id = st.session_state['therapist_id']
                st.title(f"Therapist Dashboard: {therapist_id}")
                
                tabs = st.tabs(["Create Slots", "View My Schedule", "Manage Bookings"])
                
                with tabs[0]:
                    st.header("Create Available Time Slots")
                    
                    # Date selection for new slot
                    col1, col2 = st.columns(2)
                    with col1:
                        slot_date = st.date_input(
                            "Select Date",
                            value=datetime.datetime.now().date() + timedelta(days=1),
                            min_value=datetime.datetime.now().date(),
                        )
                    
                    with col2:
                        slot_time = st.time_input(
                            "Select Start Time",
                            value=datetime.time(9, 0)
                        )
                    
                    # Create slot button
                    if st.button("Create 1-Hour Slot"):
                        slot_datetime = datetime.datetime.combine(slot_date, slot_time)
                        end_datetime = slot_datetime + timedelta(hours=1)
                        
                        success = create_free_slot(therapist_id, slot_datetime, end_datetime)
                        
                        if success:
                            st.success(f"Slot created successfully: {format_time_slot(slot_datetime, end_datetime)}")
                        else:
                            st.error("Failed to create slot. The slot may overlap with existing slots.")
                
                with tabs[1]:
                    st.header("My Schedule")
                    view_date = st.date_input(
                        "Select Date to View",
                        value=datetime.datetime.now().date(),
                    )
                    
                    # Fetch and display slots
                    if st.button("Refresh Schedule"):
                        slots = list_available_slots(therapist_id, view_date)
                        
                        if slots:
                            st.subheader(f"Your slots for {view_date.strftime('%Y-%m-%d')}:")
                            for i, slot in enumerate(slots, 1):
                                with st.container():
                                    st.markdown(f"""
                                    <div class="appointment-card">
                                        <h3>Slot {i}</h3>
                                        <p>Time: {format_time_slot(slot.start_time, slot.end_time)}</p>
                                        <p>Status: {slot.status.upper()}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.info(f"No slots found for {view_date.strftime('%Y-%m-%d')}.")
                
                with tabs[2]:
                    st.header("Manage Bookings")
                    
                    st.info("This feature will be implemented in the next version.")


            def show_client_dashboard():
                """Display client dashboard"""
                client_id = st.session_state['therapist_id']  # Using the same field for simplicity
                st.title(f"Client Dashboard: {client_id}")
                
                tabs = st.tabs(["Find Available Slots", "My Bookings"])
                
                with tabs[0]:
                    st.header("Find Available Slots")
                    
                    # Therapist selection
                    therapist_id = st.text_input("Therapist ID")
                    
                    # Date selection
                    search_date = st.date_input(
                        "Select Date",
                        value=datetime.datetime.now().date() + timedelta(days=1),
                        min_value=datetime.datetime.now().date(),
                    )
                    
                    # Search button
                    if st.button("Search Available Slots"):
                        if not therapist_id:
                            st.warning("Please enter a therapist ID.")
                        else:
                            slots = list_available_slots(therapist_id, search_date)
                            
                            if slots:
                                st.subheader(f"Available slots for {therapist_id} on {search_date.strftime('%Y-%m-%d')}:")
                                
                                for i, slot in enumerate(slots, 1):
                                    with st.container():
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.markdown(f"""
                                            <div class="appointment-card">
                                                <h3>Slot {i}</h3>
                                                <p>Time: {format_time_slot(slot.start_time, slot.end_time)}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        with col2:
                                            # Using the slot's start_time as the key to ensure uniqueness
                                            if st.button("Book", key=f"book_{slot.start_time.isoformat()}"):
                                                success = book_slot(therapist_id, slot.start_time)
                                                if success:
                                                    st.success(f"Slot booked successfully: {format_time_slot(slot.start_time, slot.end_time)}")
                                                else:
                                                    st.error("Failed to book slot. The slot might have been booked already.")
                            else:
                                st.info(f"No available slots for therapist {therapist_id} on {search_date.strftime('%Y-%m-%d')}.")
                
                with tabs[1]:
                    st.header("My Bookings")
                    
                    st.info("This feature will be implemented in the next version.")

            # Run the main function
            main()
            
        except ImportError as e:
            st.error(f"Failed to import required modules: {str(e)}")
            st.error(traceback.format_exc())
            st.info("Please make sure all dependencies are installed correctly.")
            
        except Exception as e:
            st.error(f"Error during initialization: {str(e)}")
            st.error(traceback.format_exc())
            
except Exception as e:
    st.error(f"Critical application error: {str(e)}")
    st.error(traceback.format_exc())

if __name__ == "__main__":
    # This is handled above with the try-except block
    pass 