from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

from app.integrations import (
    create_free_slot,
    create_availability_range,
    list_available_slots,
    list_all_slots,
    book_slot,
    cancel_booking,
    TimeSlot
)
from app.schemas.time_slot import TimeSlotResponse


class AppointmentService:
    """Service for managing therapist appointments and slots."""
    
    def create_slot(self, therapist_id: str, start_time: datetime, end_time: datetime) -> bool:
        """
        Create a new available slot for a therapist.
        
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
        
        # Use Calendar integration (backed by Firebase) to create the slot
        return create_free_slot(therapist_id, start_time, end_time)
    
    def create_availability_range(self, therapist_id: str, start_time: datetime, end_time: datetime, slot_duration_minutes: int = 60) -> bool:
        """
        Create multiple slots within a time range for a therapist.
        
        Args:
            therapist_id: Unique identifier for the therapist
            start_time: Start time of the availability range
            end_time: End time of the availability range
            slot_duration_minutes: Duration of each slot in minutes (default is 60)
            
        Returns:
            bool: True if slots were created successfully, False otherwise
        """
        return create_availability_range(therapist_id, start_time, end_time, slot_duration_minutes)
    
    def list_available_slots(self, therapist_id: str, search_date: date) -> List[TimeSlotResponse]:
        """
        List available slots for a therapist on a specific date.
        
        Args:
            therapist_id: Unique identifier for the therapist
            search_date: Date to search for available slots
            
        Returns:
            List[TimeSlotResponse]: List of available time slots
        """
        # Get slots from Calendar integration (backed by Firebase)
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
    
    def list_all_slots(self, therapist_id: str, search_date: date) -> List[TimeSlotResponse]:
        """
        List all slots (both free and busy) for a therapist on a specific date.
        
        Args:
            therapist_id: Unique identifier for the therapist
            search_date: Date to search for all slots
            
        Returns:
            List[TimeSlotResponse]: List of all time slots
        """
        # Get all slots from Calendar integration (backed by Firebase)
        slots = list_all_slots(therapist_id, search_date)
        
        # Convert to response model
        return [
            TimeSlotResponse(
                therapist_id=therapist_id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                status=slot.status
            ) for slot in slots
        ]
    
    def get_therapist_stats(self, therapist_id: str, search_date: date) -> Dict[str, Any]:
        """
        Get statistics for a therapist's slots on a specific date.
        
        Args:
            therapist_id: Unique identifier for the therapist
            search_date: Date to get statistics for
            
        Returns:
            Dict with therapist ID, total slots, available slots, and booked slots counts
        """
        # Get all slots
        all_slots = self.list_all_slots(therapist_id, search_date)
        
        # Count by status
        free_slots = [slot for slot in all_slots if slot.status == "free"]
        busy_slots = [slot for slot in all_slots if slot.status == "busy"]
        
        # Create stats object
        return {
            "therapist_id": therapist_id,
            "total_slots": len(all_slots),
            "available_slots": len(free_slots),
            "booked_slots": len(busy_slots),
            "date": search_date.isoformat()
        }
    
    def book_slot(self, therapist_id: str, slot_time: datetime) -> bool:
        """
        Book a slot with a therapist.
        
        Args:
            therapist_id: Unique identifier for the therapist
            slot_time: Start time of the slot to book
            
        Returns:
            bool: True if booking was successful, False otherwise
        """
        return book_slot(therapist_id, slot_time)
    
    def cancel_booking(self, therapist_id: str, slot_time: datetime) -> bool:
        """
        Cancel a booked slot.
        
        Args:
            therapist_id: Unique identifier for the therapist
            slot_time: Start time of the booked slot
            
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        return cancel_booking(therapist_id, slot_time) 