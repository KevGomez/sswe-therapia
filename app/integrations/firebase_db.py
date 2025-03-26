import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)

import firebase_admin
from firebase_admin import credentials, db

from app.config import active_config

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate(active_config.get_firebase_credentials())
    firebase_admin.initialize_app(cred, {
        'databaseURL': active_config.get_database_url()
    })
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Firebase: {e}")
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
    Get all slots for a therapist.
    
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
    Save all slots for a therapist.
    
    Args:
        therapist_id: Unique identifier for the therapist
        slots: List of slot dictionaries to save
    
    Raises:
        Exception: If there's an error saving the slots
    """
    try:
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
    Create a free slot for a therapist in the calendar.
    
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
    Create multiple free slots within a time range for a therapist.
    
    Args:
        therapist_id: Unique identifier for the therapist
        start_time: Start time of the availability range
        end_time: End time of the availability range
        slot_duration_minutes: Duration of each slot in minutes (default is 60)
        
    Returns:
        bool: True if all slots were created successfully, False otherwise
    """
    logger.info(f"Creating availability range for therapist {therapist_id} from {start_time} to {end_time}")
    
    # Calculate time slots
    current_start = start_time
    slots_created = 0
    
    # Get existing slots
    existing_slots = _get_therapist_slots(therapist_id)
    new_slots = []
    
    # Create slot objects for the entire range
    while current_start < end_time:
        slot_end = current_start + timedelta(minutes=slot_duration_minutes)
        
        # Make sure we don't go beyond the end time
        if slot_end > end_time:
            slot_end = end_time
            
        # Only create complete slots if they are at least the minimum duration
        if (slot_end - current_start).total_seconds() / 60 >= slot_duration_minutes:
            # Check for overlap with existing slots
            is_overlapping = False
            for slot_dict in existing_slots:
                slot = TimeSlot.from_dict(slot_dict)
                if (current_start < slot.end_time and slot_end > slot.start_time):
                    is_overlapping = True
                    logger.warning(f"Skipping overlapping slot: {current_start} - {slot_end}")
                    break
            
            if not is_overlapping:
                new_slot = TimeSlot(start_time=current_start, end_time=slot_end)
                new_slots.append(new_slot.to_dict())
                slots_created += 1
        
        # Move to next slot
        current_start = slot_end
    
    # If slots were created, save them
    if slots_created > 0:
        all_slots = existing_slots + new_slots
        _save_therapist_slots(therapist_id, all_slots)
        logger.info(f"Created {slots_created} slots for therapist {therapist_id}")
        return True
    
    logger.warning(f"No slots created for therapist {therapist_id}")
    return False


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
    
    # Filter slots by date only, not by status
    all_slots = []
    for slot_dict in slots:
        slot = TimeSlot.from_dict(slot_dict)
        slot_date = slot.start_time.date()
        
        if slot_date == search_date:
            all_slots.append(slot)
    
    return all_slots


def book_slot(therapist_id: str, slot_time: datetime) -> bool:
    """
    Book a slot with a therapist.
    
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
                logger.info(f"Booking failed for therapist {therapist_id}: slot already booked")
                return False
            
            # Update slot status to busy
            slots[i]["status"] = "busy"
            _save_therapist_slots(therapist_id, slots)
            logger.info(f"Slot booked successfully for therapist {therapist_id}")
            return True
    
    logger.info(f"Booking failed for therapist {therapist_id}: slot not found")
    return False  # Slot not found


def cancel_booking(therapist_id: str, slot_time: datetime) -> bool:
    """
    Cancel a booked slot.
    
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
                logger.info(f"Cancellation failed for therapist {therapist_id}: slot is not booked")
                return False
            
            # Update slot status to free
            slots[i]["status"] = "free"
            _save_therapist_slots(therapist_id, slots)
            logger.info(f"Booking cancelled successfully for therapist {therapist_id}")
            return True
    
    logger.info(f"Cancellation failed for therapist {therapist_id}: slot not found")
    return False  # Slot not found 