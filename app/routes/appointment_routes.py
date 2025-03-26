from datetime import datetime
from typing import Dict, Any, List, Tuple, Union
import logging

from flask import Blueprint, request, jsonify, Response

from app.services.appointment_service import AppointmentService
from app.schemas.time_slot import (
    TimeSlotCreate, 
    TimeSlotResponse, 
    TimeSlotBook,
    TimeSlotCancel,
    TimeSlotList
)
from app.utils.date_utils import is_valid_appointment_slot, is_valid_booking_time

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
appointment_bp = Blueprint('appointments', __name__, url_prefix='/api/appointments')
appointment_service = AppointmentService()


@appointment_bp.route('/therapist/slots', methods=['POST'])
def create_slot() -> Tuple[Response, int]:
    """
    Create a new available slot for a therapist.
    
    Request body:
    {
        "therapist_id": "123",
        "start_time": "2023-06-01T10:00:00",
        "end_time": "2023-06-01T11:00:00"
    }
    """
    try:
        data = request.get_json()
        slot_data = TimeSlotCreate(
            therapist_id=data['therapist_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time'])
        )
        
        # Validate slot
        is_valid, error_msg = is_valid_appointment_slot(slot_data.start_time, slot_data.end_time)
        if not is_valid:
            logger.warning(f"Invalid slot creation attempt: {error_msg}")
            return jsonify({"success": False, "message": error_msg}), 400
            
        # Create slot
        success = appointment_service.create_slot(
            slot_data.therapist_id,
            slot_data.start_time,
            slot_data.end_time
        )
        
        if success:
            logger.info(f"Slot created for therapist {slot_data.therapist_id}")
            return jsonify({"success": True, "message": "Slot created successfully"}), 201
        else:
            logger.warning(f"Failed to create slot for therapist {slot_data.therapist_id}")
            return jsonify({"success": False, "message": "Failed to create slot. The slot may overlap with existing slots."}), 400
            
    except Exception as e:
        logger.error(f"Error in create_slot: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/therapist/availability', methods=['POST'])
def create_availability_range() -> Tuple[Response, int]:
    """
    Create multiple available slots within a time range for a therapist.
    
    Request body:
    {
        "therapist_id": "123",
        "start_time": "2023-06-01T09:00:00",
        "end_time": "2023-06-01T17:00:00",
        "slot_duration_minutes": 60
    }
    """
    try:
        data = request.get_json()
        therapist_id = data['therapist_id']
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
        slot_duration_minutes = int(data.get('slot_duration_minutes', 60))
        
        # Validate time range
        if start_time >= end_time:
            logger.warning(f"Invalid time range: start_time must be before end_time")
            return jsonify({
                "success": False, 
                "message": "Start time must be before end time"
            }), 400
            
        # Validate slot duration
        if slot_duration_minutes < 15 or slot_duration_minutes > 120:
            logger.warning(f"Invalid slot duration: {slot_duration_minutes} minutes")
            return jsonify({
                "success": False, 
                "message": "Slot duration must be between 15 and 120 minutes"
            }), 400
            
        # Create the range of slots
        success = appointment_service.create_availability_range(
            therapist_id,
            start_time,
            end_time,
            slot_duration_minutes
        )
        
        if success:
            logger.info(f"Created availability range for therapist {therapist_id}")
            return jsonify({
                "success": True, 
                "message": "Availability range created successfully"
            }), 201
        else:
            logger.warning(f"Failed to create availability range for therapist {therapist_id}")
            return jsonify({
                "success": False, 
                "message": "Failed to create availability range. There may be overlapping slots."
            }), 400
            
    except Exception as e:
        logger.error(f"Error in create_availability_range: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/therapist/<therapist_id>/slots', methods=['GET'])
def list_slots(therapist_id: str) -> Tuple[Response, int]:
    """
    List all slots for a therapist.
    
    Query parameters:
    - date: Date to list slots for (YYYY-MM-DD)
    """
    try:
        date_str = request.args.get('date')
        if not date_str:
            logger.warning("Date parameter missing in list_slots request")
            return jsonify({"success": False, "message": "Date parameter is required"}), 400
            
        date_obj = datetime.fromisoformat(date_str)
        
        # Get all slots (both free and busy)
        slots = appointment_service.list_all_slots(therapist_id, date_obj.date())
        
        # Convert to dict for response
        slots_data = [
            {
                "therapist_id": slot.therapist_id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "status": slot.status
            } for slot in slots
        ]
        
        logger.info(f"Retrieved {len(slots_data)} slots for therapist {therapist_id}")
        return jsonify({"success": True, "slots": slots_data}), 200
        
    except Exception as e:
        logger.error(f"Error in list_slots: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/therapist/<therapist_id>/stats', methods=['GET'])
def get_therapist_stats(therapist_id: str) -> Tuple[Response, int]:
    """
    Get statistics for a therapist's slots on a specific date.
    
    Query parameters:
    - date: Date to get statistics for (YYYY-MM-DD)
    """
    try:
        date_str = request.args.get('date')
        if not date_str:
            logger.warning("Date parameter missing in get_therapist_stats request")
            return jsonify({"success": False, "message": "Date parameter is required"}), 400
            
        date_obj = datetime.fromisoformat(date_str)
        
        # Get therapist stats
        stats = appointment_service.get_therapist_stats(therapist_id, date_obj.date())
        
        logger.info(f"Retrieved stats for therapist {therapist_id}")
        return jsonify({
            "success": True, 
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_therapist_stats: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/therapists', methods=['GET'])
def list_therapists() -> Tuple[Response, int]:
    """
    List all therapists with their availability statistics for a specific date.
    
    Query parameters:
    - date: Date to list therapists for (YYYY-MM-DD)
    - therapist_ids: Comma-separated list of therapist IDs to include (optional)
    """
    try:
        date_str = request.args.get('date')
        if not date_str:
            logger.warning("Date parameter missing in list_therapists request")
            return jsonify({"success": False, "message": "Date parameter is required"}), 400
            
        date_obj = datetime.fromisoformat(date_str)
        
        # Get list of therapist IDs (comma-separated string)
        therapist_ids_str = request.args.get('therapist_ids', '')
        
        # If therapist_ids is provided, split and process them
        therapist_stats = []
        if therapist_ids_str:
            therapist_ids = [tid.strip() for tid in therapist_ids_str.split(',')]
            
            # Get stats for each therapist
            for therapist_id in therapist_ids:
                stats = appointment_service.get_therapist_stats(therapist_id, date_obj.date())
                if stats["total_slots"] > 0:  # Only include therapists with slots
                    therapist_stats.append(stats)
        else:
            # If no therapist IDs were provided, we could return an error or
            # we could implement a way to discover all therapists in the system
            logger.warning("No therapist IDs provided in list_therapists request")
            return jsonify({
                "success": False, 
                "message": "Please provide a comma-separated list of therapist IDs using the therapist_ids parameter"
            }), 400
        
        logger.info(f"Retrieved stats for {len(therapist_stats)} therapists")
        return jsonify({
            "success": True,
            "date": date_obj.date().isoformat(),
            "therapists": therapist_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in list_therapists: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/book', methods=['POST'])
def book_slot() -> Tuple[Response, int]:
    """
    Book a slot with a therapist.
    
    Request body:
    {
        "therapist_id": "123",
        "slot_time": "2023-06-01T10:00:00"
    }
    """
    try:
        data = request.get_json()
        booking_data = TimeSlotBook(
            therapist_id=data['therapist_id'],
            slot_time=datetime.fromisoformat(data['slot_time'])
        )
        
        # Validate booking time
        is_valid, error_msg = is_valid_booking_time(booking_data.slot_time)
        if not is_valid:
            logger.warning(f"Invalid booking attempt: {error_msg}")
            return jsonify({"success": False, "message": error_msg}), 400
            
        # Book slot
        success = appointment_service.book_slot(
            booking_data.therapist_id,
            booking_data.slot_time
        )
        
        if success:
            logger.info(f"Slot booked for therapist {booking_data.therapist_id}")
            return jsonify({"success": True, "message": "Slot booked successfully"}), 200
        else:
            logger.warning(f"Failed to book slot for therapist {booking_data.therapist_id}")
            return jsonify({"success": False, "message": "Failed to book slot. The slot may not exist or is already booked."}), 400
            
    except Exception as e:
        logger.error(f"Error in book_slot: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/cancel', methods=['POST'])
def cancel_booking() -> Tuple[Response, int]:
    """
    Cancel a booked slot.
    
    Request body:
    {
        "therapist_id": "123",
        "slot_time": "2023-06-01T10:00:00"
    }
    """
    try:
        data = request.get_json()
        cancel_data = TimeSlotCancel(
            therapist_id=data['therapist_id'],
            slot_time=datetime.fromisoformat(data['slot_time'])
        )
        
        # Cancel booking
        success = appointment_service.cancel_booking(
            cancel_data.therapist_id,
            cancel_data.slot_time
        )
        
        if success:
            logger.info(f"Booking canceled for therapist {cancel_data.therapist_id}")
            return jsonify({"success": True, "message": "Booking canceled successfully"}), 200
        else:
            logger.warning(f"Failed to cancel booking for therapist {cancel_data.therapist_id}")
            return jsonify({"success": False, "message": "Failed to cancel booking. The slot may not exist or is not booked."}), 400
            
    except Exception as e:
        logger.error(f"Error in cancel_booking: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400 