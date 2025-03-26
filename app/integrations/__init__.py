# Import main functions from database module
try:
    # First try firebase
    from app.integrations.firebase_db import (
        TimeSlot,
        create_free_slot,
        create_availability_range,
        list_available_slots,
        list_all_slots,
        book_slot,
        cancel_booking
    )
except ImportError:
    # Fallback to google calendar
    from app.integrations.google_calendar import (
        TimeSlot,
        create_free_slot,
        create_availability_range,
        list_available_slots,
        list_all_slots,
        book_slot,
        cancel_booking
    )

__all__ = [
    'TimeSlot',
    'create_free_slot',
    'create_availability_range',
    'list_available_slots',
    'list_all_slots',
    'book_slot',
    'cancel_booking'
]
