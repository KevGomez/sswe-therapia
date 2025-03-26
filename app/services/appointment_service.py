from datetime import datetime, date, timedelta
from typing import List, Optional

from app.integrations import (
    create_free_slot,
    list_available_slots,
    book_slot,
    cancel_booking,
    TimeSlot
)
from app.schemas.time_slot import TimeSlotResponse


class AppointmentService:
    """Service for managing appointments"""
    
    @staticmethod
    def create_slot(therapist_id: str, start_time: datetime, end_time: datetime) -> bool:
        """
        Create a new available slot for a therapist
        
        Args:
            therapist_id: Unique identifier for the therapist
            start_time: Start time of the slot
            end_time: End time of the slot
            
        Returns:
            bool: True if slot was created successfully, False otherwise
        """
        # Validate slot duration (must be exactly 1 hour)
        if end_time - start_time != timedelta(hours=1):
            return False
        
        # Use Google Calendar integration (backed by Firebase) to create the slot
        return create_free_slot(therapist_id, start_time, end_time)
    
    @staticmethod
    def list_available_slots(therapist_id: str, search_date: date) -> List[TimeSlotResponse]:
        """
        List available slots for a therapist on a specific date
        
        Args:
            therapist_id: Unique identifier for the therapist
            search_date: Date to search for available slots
            
        Returns:
            List[TimeSlotResponse]: List of available time slots
        """
        # Get slots from Google Calendar integration (backed by Firebase)
        slots = list_available_slots(therapist_id, search_date)
        
        # Convert to response model
        return [
            TimeSlotResponse(
                therapist_id=therapist_id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                status=slot.status
            ) for slot in slots
        ]
    
    @staticmethod
    def book_slot(therapist_id: str, slot_time: datetime) -> bool:
        """
        Book a slot with a therapist
        
        Args:
            therapist_id: Unique identifier for the therapist
            slot_time: Start time of the slot to book
            
        Returns:
            bool: True if booking was successful, False otherwise
        """
        return book_slot(therapist_id, slot_time)
    
    @staticmethod
    def cancel_booking(therapist_id: str, slot_time: datetime) -> bool:
        """
        Cancel a booked slot
        
        Args:
            therapist_id: Unique identifier for the therapist
            slot_time: Start time of the booked slot
            
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        return cancel_booking(therapist_id, slot_time) 