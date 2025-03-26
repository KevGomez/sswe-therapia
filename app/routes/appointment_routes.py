from datetime import datetime
from typing import Dict, Any, List, Tuple, Union

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

# Create Blueprint
appointment_bp = Blueprint('appointments', __name__, url_prefix='/api/appointments')
appointment_service = AppointmentService()


@appointment_bp.route('/therapist/slots', methods=['POST'])
def create_slot() -> Tuple[Response, int]:
    """
    Create a new available slot for a therapist
    
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
            return jsonify({"success": False, "message": error_msg}), 400
            
        # Create slot
        success = appointment_service.create_slot(
            slot_data.therapist_id,
            slot_data.start_time,
            slot_data.end_time
        )
        
        if success:
            return jsonify({"success": True, "message": "Slot created successfully"}), 201
        else:
            return jsonify({"success": False, "message": "Failed to create slot. The slot may overlap with existing slots."}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/therapist/<therapist_id>/slots', methods=['GET'])
def list_slots(therapist_id: str) -> Tuple[Response, int]:
    """
    List available slots for a therapist
    
    Query parameters:
    - date: Date to list available slots for (YYYY-MM-DD)
    """
    try:
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({"success": False, "message": "Date parameter is required"}), 400
            
        date_obj = datetime.fromisoformat(date_str)
        
        # Get available slots
        slots = appointment_service.list_available_slots(therapist_id, date_obj.date())
        
        # Convert to dict for response
        slots_data = [
            {
                "therapist_id": slot.therapist_id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "status": slot.status
            } for slot in slots
        ]
        
        return jsonify({"success": True, "slots": slots_data}), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/book', methods=['POST'])
def book_slot() -> Tuple[Response, int]:
    """
    Book a slot with a therapist
    
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
            return jsonify({"success": False, "message": error_msg}), 400
            
        # Book slot
        success = appointment_service.book_slot(
            booking_data.therapist_id,
            booking_data.slot_time
        )
        
        if success:
            return jsonify({"success": True, "message": "Slot booked successfully"}), 200
        else:
            return jsonify({"success": False, "message": "Failed to book slot. The slot may not exist or is already booked."}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@appointment_bp.route('/cancel', methods=['POST'])
def cancel_booking() -> Tuple[Response, int]:
    """
    Cancel a booked slot
    
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
            return jsonify({"success": True, "message": "Booking canceled successfully"}), 200
        else:
            return jsonify({"success": False, "message": "Failed to cancel booking. The slot may not exist or is not booked."}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400 