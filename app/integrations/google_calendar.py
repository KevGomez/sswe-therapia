from datetime import datetime, date
from typing import List, Dict, Any, Optional
import os
import streamlit as st  # Import streamlit
from dotenv import load_dotenv

# Load environment variables for local development
if not hasattr(st, 'secrets'):  # Only load dotenv if not running in Streamlit Cloud
    load_dotenv()

import firebase_admin
from firebase_admin import credentials, db

# Helper function to get Firebase credentials
def get_firebase_credentials():
    # Try to get from Streamlit secrets first
    if hasattr(st, 'secrets') and 'firebase' in st.secrets:
        return {
            "type": "service_account",
            "project_id": "sansa-sswe-kevin",
            "private_key_id": st.secrets.firebase.FIREBASE_PRIVATE_KEY_ID,
            "private_key": st.secrets.firebase.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
            "client_email": st.secrets.firebase.FIREBASE_CLIENT_EMAIL,
            "client_id": st.secrets.firebase.FIREBASE_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": st.secrets.firebase.FIREBASE_CLIENT_CERT_URL
        }
    # Fall back to environment variables
    else:
        return {
            "type": "service_account",
            "project_id": "sansa-sswe-kevin",
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
        }

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(get_firebase_credentials())
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://sansa-sswe-kevin-default-rtdb.firebaseio.com/'
        })
        print("Firebase initialized successfully in google_calendar.py")
    except Exception as e:
        print(f"Error initializing Firebase in google_calendar.py: {e}")
        raise

# Get a reference to the database
db_ref = db.reference('appointments')

class TimeSlot:
    def __init__(self, start_time: datetime, end_time: datetime, status: str = "free"):
        self.start_time = start_time
        self.end_time = end_time
        self.status = status  # 'free' or 'busy'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeSlot':
        return cls(
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            status=data["status"]
        )


def _get_therapist_slots(therapist_id: str) -> List[Dict[str, Any]]:
    """Get all slots for a therapist from Firebase"""
    try:
        therapist_ref = db_ref.child(therapist_id)
        slots_data = therapist_ref.get()
        print(f"[GCal] Retrieved slots for therapist {therapist_id}: {slots_data}")
        if slots_data is None:
            return []
        if isinstance(slots_data, list):
            return slots_data
        # If it's not a list, return an empty list to maintain type safety
        print(f"[GCal] Warning: Unexpected data format. Expected list, got {type(slots_data)}")
        return []
    except Exception as e:
        print(f"[GCal] Error getting slots: {e}")
        return []


def _save_therapist_slots(therapist_id: str, slots: List[Dict[str, Any]]) -> None:
    """Save all slots for a therapist to Firebase"""
    try:
        print(f"[GCal] Attempting to save slots for therapist {therapist_id}")
        print(f"[GCal] Data to save: {slots}")
        therapist_ref = db_ref.child(therapist_id)
        therapist_ref.set(slots)
        # Verify the data was saved
        saved_data = therapist_ref.get()
        print(f"[GCal] Verified saved data: {saved_data}")
        if saved_data != slots:
            print("[GCal] Warning: Saved data does not match input data")
    except Exception as e:
        print(f"[GCal] Error saving slots: {str(e)}")
        print(f"[GCal] Error type: {type(e)}")
        raise


def create_free_slot(therapist_id: str, start_time: datetime, end_time: datetime) -> bool:
    """
    Create a free slot for a therapist in the calendar
    
    Args:
        therapist_id: Unique identifier for the therapist
        start_time: Start time of the slot
        end_time: End time of the slot
        
    Returns:
        bool: True if slot was created successfully, False otherwise
    """
    # Get existing slots
    slots = _get_therapist_slots(therapist_id)
    
    # Check for overlapping slots
    for slot_dict in slots:
        slot = TimeSlot.from_dict(slot_dict)
        # Check if new slot overlaps with existing slots
        if (start_time < slot.end_time and end_time > slot.start_time):
            return False  # Overlapping slot
    
    # Create new slot
    new_slot = TimeSlot(start_time=start_time, end_time=end_time)
    slots.append(new_slot.to_dict())
    
    # Save updated slots
    _save_therapist_slots(therapist_id, slots)
    
    return True


def list_available_slots(therapist_id: str, search_date: date) -> List[TimeSlot]:
    """
    List available (free) slots for a therapist on a specific date
    
    Args:
        therapist_id: Unique identifier for the therapist
        search_date: Date to search for available slots
        
    Returns:
        List[TimeSlot]: List of available time slots
    """
    # Get slots
    slots = _get_therapist_slots(therapist_id)
    
    # Filter slots by date and status
    available_slots = []
    for slot_dict in slots:
        slot = TimeSlot.from_dict(slot_dict)
        slot_date = slot.start_time.date()
        
        if slot_date == search_date and slot.status == "free":
            available_slots.append(slot)
    
    return available_slots


def book_slot(therapist_id: str, slot_time: datetime) -> bool:
    """
    Book a slot with a therapist
    
    Args:
        therapist_id: Unique identifier for the therapist
        slot_time: Start time of the slot to book
        
    Returns:
        bool: True if booking was successful, False otherwise
    """
    # Get slots
    slots = _get_therapist_slots(therapist_id)
    
    # Find and update the slot
    for i, slot_dict in enumerate(slots):
        slot = TimeSlot.from_dict(slot_dict)
        
        # Check if this is the slot we want to book
        if slot.start_time == slot_time:
            # Check if slot is already booked
            if slot.status == "busy":
                return False
            
            # Update slot status to busy
            slots[i]["status"] = "busy"
            _save_therapist_slots(therapist_id, slots)
            return True
    
    return False  # Slot not found


def cancel_booking(therapist_id: str, slot_time: datetime) -> bool:
    """
    Cancel a booked slot
    
    Args:
        therapist_id: Unique identifier for the therapist
        slot_time: Start time of the booked slot
        
    Returns:
        bool: True if cancellation was successful, False otherwise
    """
    # Get slots
    slots = _get_therapist_slots(therapist_id)
    
    # Find and update the slot
    for i, slot_dict in enumerate(slots):
        slot = TimeSlot.from_dict(slot_dict)
        
        # Check if this is the slot we want to cancel
        if slot.start_time == slot_time:
            # Check if slot is actually booked
            if slot.status == "free":
                return False
            
            # Update slot status to free
            slots[i]["status"] = "free"
            _save_therapist_slots(therapist_id, slots)
            return True
    
    return False  # Slot not found 