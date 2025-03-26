from datetime import datetime
from pydantic import BaseModel, Field, validator


class TimeSlotBase(BaseModel):
    """Base model for time slots"""
    start_time: datetime = Field(..., description="Start time of the slot")
    end_time: datetime = Field(..., description="End time of the slot")
    
    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
    @validator('start_time', 'end_time')
    def time_must_be_rounded_to_hour(cls, v):
        if v.minute != 0 or v.second != 0 or v.microsecond != 0:
            raise ValueError('time must be rounded to the hour')
        return v


class TimeSlotCreate(TimeSlotBase):
    """Model for creating a new time slot"""
    therapist_id: str = Field(..., description="Unique identifier for the therapist")


class TimeSlotResponse(TimeSlotBase):
    """Model for returning a time slot"""
    therapist_id: str = Field(..., description="Unique identifier for the therapist")
    status: str = Field(..., description="Status of the slot (free/busy)")


class TimeSlotBook(BaseModel):
    """Model for booking a time slot"""
    therapist_id: str = Field(..., description="Unique identifier for the therapist")
    slot_time: datetime = Field(..., description="Start time of the slot to book")


class TimeSlotCancel(BaseModel):
    """Model for canceling a booked time slot"""
    therapist_id: str = Field(..., description="Unique identifier for the therapist")
    slot_time: datetime = Field(..., description="Start time of the booked slot")


class TimeSlotList(BaseModel):
    """Model for listing available time slots"""
    therapist_id: str = Field(..., description="Unique identifier for the therapist")
    date: datetime = Field(..., description="Date to list available slots for")
    
    @validator('date')
    def only_date_part_matters(cls, v):
        # Remove time component
        return datetime(v.year, v.month, v.day) 