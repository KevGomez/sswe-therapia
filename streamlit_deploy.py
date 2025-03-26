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
            from app.integrations import (
                create_free_slot,
                list_available_slots,
                book_slot,
                cancel_booking,
                TimeSlot
            )
            from app.utils.date_utils import format_time_slot
            from app.schemas.time_slot import TimeSlotResponse
            
            st.success("Successfully loaded all components!")
            
            # Remove the debug info once loaded successfully
            st.empty()
            
            # Session state initialization
            if 'therapist_id' not in st.session_state:
                st.session_state['therapist_id'] = ''
            if 'user_role' not in st.session_state:
                st.session_state['user_role'] = None
                
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