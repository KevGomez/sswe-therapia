from datetime import datetime, timedelta
from typing import Tuple


def is_valid_appointment_slot(start_time: datetime, end_time: datetime) -> Tuple[bool, str]:
    """
    Validate if a time slot is valid for an appointment
    
    Args:
        start_time: Start time of the slot
        end_time: End time of the slot
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Check if end_time is after start_time
    if end_time <= start_time:
        return False, "End time must be after start time"
    
    # Check if slot is exactly 1 hour
    if end_time - start_time != timedelta(hours=1):
        return False, "Appointment slots must be exactly 1 hour"
    
    # Check if times are rounded to the hour
    if start_time.minute != 0 or start_time.second != 0 or start_time.microsecond != 0:
        return False, "Start time must be rounded to the hour"
    
    if end_time.minute != 0 or end_time.second != 0 or end_time.microsecond != 0:
        return False, "End time must be rounded to the hour"
    
    return True, ""


def is_valid_booking_time(slot_time: datetime) -> Tuple[bool, str]:
    """
    Validate if a booking time is valid
    
    Args:
        slot_time: Start time of the slot to book
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Check if time is in the future
    if slot_time <= datetime.now():
        return False, "Booking time must be in the future"
    
    # Check if time is rounded to the hour
    if slot_time.minute != 0 or slot_time.second != 0 or slot_time.microsecond != 0:
        return False, "Booking time must be rounded to the hour"
    
    return True, ""


def format_time_slot(start_time: datetime, end_time: datetime) -> str:
    """
    Format a time slot for display
    
    Args:
        start_time: Start time of the slot
        end_time: End time of the slot
        
    Returns:
        str: Formatted time slot string
    """
    start_str = start_time.strftime("%Y-%m-%d %H:%M")
    end_str = end_time.strftime("%H:%M")
    return f"{start_str} - {end_str}" 