from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

import firebase_admin
from firebase_admin import credentials, db

from app.config import active_config

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(active_config.get_firebase_credentials())
        firebase_admin.initialize_app(cred, {
            'databaseURL': active_config.get_database_url()
        })
        logger.info("Firebase initialized successfully in google_calendar.py")
    except Exception as e:
        logger.error(f"Error initializing Firebase in google_calendar.py: {e}")
        raise

# Get a reference to the database
db_ref = db.reference('appointments')

class TimeSlot:
    """Represents a time slot for a therapist appointment."""
    
    def __init__(self, start_time: datetime, end_time: datetime, status: str = "free"):
        """
        Initialize a new TimeSlot.
        
        Args:
            start_time: Start time of the appointment slot
            end_time: End time of the appointment slot
            status: Status of the slot - 'free' or 'busy'
        """
        self.start_time = start_time
        self.end_time = end_time
        self.status = status  # 'free' or 'busy'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the TimeSlot to a dictionary for storage."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeSlot':
        """Create a TimeSlot from a dictionary."""
        return cls(
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            status=data["status"]
        )


def _get_therapist_slots(therapist_id: str) -> List[Dict[str, Any]]:
    """
    Get all slots for a therapist from Firebase.
    
    Args:
        therapist_id: Unique identifier for the therapist
    
    Returns:
        List of slot dictionaries
    """
    try:
        therapist_ref = db_ref.child(therapist_id)
        slots_data = therapist_ref.get()
        
        if slots_data is None:
            return []
            
        if isinstance(slots_data, list):
            return slots_data
            
        # If it's not a list, return an empty list to maintain type safety
        logger.warning(f"Unexpected data format for therapist {therapist_id}. Expected list, got {type(slots_data)}")
        return []
    except Exception as e:
        logger.error(f"Error getting slots for therapist {therapist_id}: {e}")
        return []


def _save_therapist_slots(therapist_id: str, slots: List[Dict[str, Any]]) -> None:
    """
    Save all slots for a therapist to Firebase.
    
    Args:
        therapist_id: Unique identifier for the therapist
        slots: List of slot dictionaries to save
    
    Raises:
        Exception: If there's an error saving the slots
    """
    try:
        logger.debug(f"Saving slots for therapist {therapist_id}")
        therapist_ref = db_ref.child(therapist_id)
        therapist_ref.set(slots)
        
        # Verify the data was saved
        saved_data = therapist_ref.get()
        if saved_data != slots:
            logger.warning(f"Data verification failed for therapist {therapist_id}: saved data does not match input data")
    except Exception as e:
        logger.error(f"Error saving slots for therapist {therapist_id}: {e}")
        raise


def create_free_slot(therapist_id: str, start_time: datetime, end_time: datetime) -> bool:
    """
    Create a free slot for a therapist.
    
    Note: This is a mock Google Calendar API implementation that actually uses Firebase.
    
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
            logger.info(f"Slot creation failed for therapist {therapist_id}: overlapping slot found")
            return False  # Overlapping slot
    
    # Create new slot
    new_slot = TimeSlot(start_time=start_time, end_time=end_time)
    slots.append(new_slot.to_dict())
    
    # Save updated slots
    _save_therapist_slots(therapist_id, slots)
    logger.info(f"Slot created successfully for therapist {therapist_id}")
    
    return True


def create_availability_range(therapist_id: str, start_time: datetime, end_time: datetime, slot_duration_minutes: int = 60) -> bool:
    """
    Create multiple free slots for a therapist within a time range.
    
    Args:
        therapist_id: Unique identifier for the therapist
        start_time: Start time of the availability range
        end_time: End time of the availability range
        slot_duration_minutes: Duration of each slot in minutes (default is 60)
        
    Returns:
        bool: True if all slots were created successfully, False otherwise
    """
    if slot_duration_minutes <= 0:
        logger.error(f"Invalid slot duration: {slot_duration_minutes} minutes")
        return False

    if start_time >= end_time:
        logger.error(f"Invalid time range: start time {start_time} is not before end time {end_time}")
        return False

    slots_created = 0
    current_start = start_time
    
    # Create slots until we've filled the entire range
    while current_start + timedelta(minutes=slot_duration_minutes) <= end_time:
        current_end = current_start + timedelta(minutes=slot_duration_minutes)
        
        # Try to create the slot
        if create_free_slot(therapist_id, current_start, current_end):
            slots_created += 1
        
        # Move to the next slot
        current_start = current_end
    
    logger.info(f"Created {slots_created} slots for therapist {therapist_id} in range {start_time} to {end_time}")
    return slots_created > 0


def list_available_slots(therapist_id: str, search_date: date) -> List[TimeSlot]:
    """
    List available (free) slots for a therapist on a specific date.
    
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


def list_all_slots(therapist_id: str, search_date: date) -> List[TimeSlot]:
    """
    List all slots (both free and busy) for a therapist on a specific date.
    
    Args:
        therapist_id: Unique identifier for the therapist
        search_date: Date to search for slots
        
    Returns:
        List[TimeSlot]: List of all time slots
    """
    # Get slots
    slots = _get_therapist_slots(therapist_id)
    
    # Filter slots by date
    filtered_slots = []
    for slot_dict in slots:
        slot = TimeSlot.from_dict(slot_dict)
        slot_date = slot.start_time.date()
        
        if slot_date == search_date:
            filtered_slots.append(slot)
    
    return filtered_slots


def book_slot(therapist_id: str, slot_time: datetime) -> bool:
    """
    Book a slot for a therapist.
    
    Args:
        therapist_id: Unique identifier for the therapist
        slot_time: Start time of the slot to book
        
    Returns:
        bool: True if slot was booked successfully, False otherwise
    """
    # Get slots
    slots = _get_therapist_slots(therapist_id)
    
    # Find the slot to book
    for i, slot_dict in enumerate(slots):
        slot = TimeSlot.from_dict(slot_dict)
        
        # Check if this is the slot we want to book
        if slot.start_time == slot_time:
            # Check if slot is already booked
            if slot.status == "busy":
                logger.info(f"Slot booking failed for therapist {therapist_id}: slot is already booked")
                return False
            
            # Update the slot status to booked
            slot.status = "busy"
            slots[i] = slot.to_dict()
            
            # Save updated slots
            _save_therapist_slots(therapist_id, slots)
            logger.info(f"Slot booked successfully for therapist {therapist_id}")
            
            return True
    
    logger.info(f"Slot booking failed for therapist {therapist_id}: slot not found")
    return False


def cancel_booking(therapist_id: str, slot_time: datetime) -> bool:
    """
    Cancel a booking for a therapist.
    
    Args:
        therapist_id: Unique identifier for the therapist
        slot_time: Start time of the slot to cancel
        
    Returns:
        bool: True if booking was canceled successfully, False otherwise
    """
    # Get slots
    slots = _get_therapist_slots(therapist_id)
    
    # Find the slot to cancel
    for i, slot_dict in enumerate(slots):
        slot = TimeSlot.from_dict(slot_dict)
        
        # Check if this is the slot we want to cancel
        if slot.start_time == slot_time:
            # Check if slot is actually booked
            if slot.status == "free":
                logger.info(f"Booking cancellation failed for therapist {therapist_id}: slot is not booked")
                return False
            
            # Update the slot status to free
            slot.status = "free"
            slots[i] = slot.to_dict()
            
            # Save updated slots
            _save_therapist_slots(therapist_id, slots)
            logger.info(f"Booking canceled successfully for therapist {therapist_id}")
            
            return True
    
    logger.info(f"Booking cancellation failed for therapist {therapist_id}: slot not found")
    return False 