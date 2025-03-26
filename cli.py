#!/usr/bin/env python3
"""
CLI tool for interacting with the Therapist-Client Scheduling API.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
import os
from typing import Optional, Dict, Any, List

from app.integrations import (
    create_free_slot,
    list_available_slots,
    book_slot,
    cancel_booking,
    TimeSlot
)
from app.utils.date_utils import format_time_slot


def create_slot_cmd(args: argparse.Namespace) -> None:
    """Create a new available slot for a therapist"""
    try:
        start_time = datetime.datetime.fromisoformat(args.start_time)
        end_time = datetime.datetime.fromisoformat(args.end_time)
        
        # Create slot using Google Calendar API (backed by Firebase)
        success = create_free_slot(args.therapist_id, start_time, end_time)
        
        if success:
            print(f"✅ Slot created successfully: {format_time_slot(start_time, end_time)}")
        else:
            print("❌ Failed to create slot. The slot may overlap with existing slots.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def list_slots_cmd(args: argparse.Namespace) -> None:
    """List available slots for a therapist"""
    try:
        date_obj = datetime.datetime.fromisoformat(args.date).date()
        
        # Get available slots using Google Calendar API (backed by Firebase)
        slots = list_available_slots(args.therapist_id, date_obj)
        
        if slots:
            print(f"Available slots for therapist {args.therapist_id} on {date_obj.isoformat()}:")
            for i, slot in enumerate(slots, 1):
                print(f"  {i}. {format_time_slot(slot.start_time, slot.end_time)}")
        else:
            print(f"No available slots for therapist {args.therapist_id} on {date_obj.isoformat()}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def book_slot_cmd(args: argparse.Namespace) -> None:
    """Book a slot with a therapist"""
    try:
        slot_time = datetime.datetime.fromisoformat(args.slot_time)
        
        # Book slot using Google Calendar API (backed by Firebase)
        success = book_slot(args.therapist_id, slot_time)
        
        if success:
            print(f"✅ Slot booked successfully: {slot_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("❌ Failed to book slot. The slot may not exist or is already booked.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def cancel_booking_cmd(args: argparse.Namespace) -> None:
    """Cancel a booked slot"""
    try:
        slot_time = datetime.datetime.fromisoformat(args.slot_time)
        
        # Cancel booking using Google Calendar API (backed by Firebase)
        success = cancel_booking(args.therapist_id, slot_time)
        
        if success:
            print(f"✅ Booking canceled successfully: {slot_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("❌ Failed to cancel booking. The slot may not exist or is not booked.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def main() -> None:
    """Main CLI entrypoint"""
    parser = argparse.ArgumentParser(description="Therapist-Client Scheduling CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create slot command
    create_parser = subparsers.add_parser("create-slot", help="Create a new available slot for a therapist")
    create_parser.add_argument("therapist_id", help="Unique identifier for the therapist")
    create_parser.add_argument("start_time", help="Start time of the slot (ISO format: YYYY-MM-DDTHH:MM:SS)")
    create_parser.add_argument("end_time", help="End time of the slot (ISO format: YYYY-MM-DDTHH:MM:SS)")
    create_parser.set_defaults(func=create_slot_cmd)
    
    # List slots command
    list_parser = subparsers.add_parser("list-slots", help="List available slots for a therapist")
    list_parser.add_argument("therapist_id", help="Unique identifier for the therapist")
    list_parser.add_argument("date", help="Date to list available slots for (ISO format: YYYY-MM-DD)")
    list_parser.set_defaults(func=list_slots_cmd)
    
    # Book slot command
    book_parser = subparsers.add_parser("book-slot", help="Book a slot with a therapist")
    book_parser.add_argument("therapist_id", help="Unique identifier for the therapist")
    book_parser.add_argument("slot_time", help="Start time of the slot to book (ISO format: YYYY-MM-DDTHH:MM:SS)")
    book_parser.set_defaults(func=book_slot_cmd)
    
    # Cancel booking command
    cancel_parser = subparsers.add_parser("cancel-booking", help="Cancel a booked slot")
    cancel_parser.add_argument("therapist_id", help="Unique identifier for the therapist")
    cancel_parser.add_argument("slot_time", help="Start time of the booked slot (ISO format: YYYY-MM-DDTHH:MM:SS)")
    cancel_parser.set_defaults(func=cancel_booking_cmd)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
        
    # Run command
    args.func(args)


if __name__ == "__main__":
    main() 