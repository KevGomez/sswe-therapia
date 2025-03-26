# Integration modules for database access
#
# The application supports two compatible database backends:
# 1. Firebase Realtime Database (primary implementation)
# 2. Google Calendar Mock (alternative implementation using Firebase under the hood)
#
# Both implementations provide the same interface and functionality.
# The architecture allows for easy switching between implementations
# or adding new ones in the future.

import logging

logger = logging.getLogger(__name__)

# Try to import from firebase first (primary implementation)
try:
    from app.integrations.firebase_db import (
        TimeSlot,
        create_free_slot,
        create_availability_range,
        list_available_slots,
        list_all_slots,
        book_slot,
        cancel_booking
    )
    logger.info("Using Firebase DB implementation")
except ImportError:
    # Fall back to Google Calendar mock if Firebase is unavailable
    logger.info("Firebase implementation not found, falling back to Google Calendar mock")
    from app.integrations.google_calendar import (
        TimeSlot,
        create_free_slot,
        create_availability_range,
        list_available_slots,
        list_all_slots,
        book_slot,
        cancel_booking
    )

# Export the public API
__all__ = [
    'TimeSlot',
    'create_free_slot',
    'create_availability_range',
    'list_available_slots',
    'list_all_slots',
    'book_slot',
    'cancel_booking'
]
