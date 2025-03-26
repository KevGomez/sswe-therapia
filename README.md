# Therapist-Client Scheduling System

A Flask-based web application for managing therapist-client appointments.

## Demo

- URL: `https://drive.google.com/file/d/1BXs6D-pzsd7Zs7q9b-IiEikLRGCWqClN/view?usp=share_link`

## Features

- Therapists can create availability slots individually or in time ranges
- Clients can search for therapists with available slots on specific dates
- Clients can view and book available slots with a specific therapist
- Therapists can view their complete schedule (both available and booked slots)
- Double bookings are prevented through validation
- Therapists can cancel bookings
- Clean, responsive UI built with Bootstrap 5
- Modern interface with filtering and sorting capabilities

## Tech Stack

- **Backend:**

  - Python 3.8+
  - Flask (Web framework)
  - Firebase Realtime Database (Data storage)
  - Pydantic (Data validation)

- **Frontend:**
  - Bootstrap 5 (UI framework)
  - Vanilla JavaScript (Client-side logic)
  - FontAwesome (Icons)

## Architecture

The application follows a layered architecture pattern:

1. **Presentation Layer** - Flask routes and HTML templates
2. **Service Layer** - AppointmentService class for business logic
3. **Data Access Layer** - Integration modules for database interactions

The system is designed with modularity in mind:

- The database integration is abstracted behind a common interface
- Multiple backend implementations can be used interchangeably
- Modern OOP principles are applied throughout the codebase

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Firebase project with Realtime Database enabled
- Firebase service account credentials

## Project Setup

1. Clone the repository

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Set up Firebase:

   - Go to Firebase Console (https://console.firebase.google.com)
   - Select your project
   - Enable Realtime Database
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file
   - Copy the values from the JSON file to your `.env` file:
     ```
     FIREBASE_PRIVATE_KEY_ID=<from_json>
     FIREBASE_PRIVATE_KEY=<from_json>
     FIREBASE_CLIENT_EMAIL=<from_json>
     FIREBASE_CLIENT_ID=<from_json>
     FIREBASE_CLIENT_CERT_URL=<from_json>
     ```

6. Run the application:
   ```bash
   python main.py
   ```

By default, the application runs on `http://0.0.0.0:5001`.

## Environment Variables

You can customize the application using the following environment variables:

- `FLASK_HOST`: Host to run the server on (default: "0.0.0.0")
- `FLASK_PORT`: Port to run the server on (default: 5001)
- `FLASK_DEBUG`: Enable debug mode (default: True)
- `SECRET_KEY`: Flask secret key (default: "dev")
- Firebase credentials (required):
  - `FIREBASE_PRIVATE_KEY_ID`
  - `FIREBASE_PRIVATE_KEY`
  - `FIREBASE_CLIENT_EMAIL`
  - `FIREBASE_CLIENT_ID`
  - `FIREBASE_CLIENT_CERT_URL`

## Web User Interface

The application provides a web-based user interface with separate portals for therapists and clients:

### Home Page

- Overview of the system
- Links to both therapist and client portals

### Therapist Portal

- Create new availability slots by specifying date and time
- Create multiple slots at once by specifying a time range and slot duration
- View complete schedule with filtering options for available and booked slots
- Cancel bookings directly from the schedule view
- View statistics about available and booked slots

### Client Portal

- Search for therapists with availability on specific dates
- View therapist availability statistics
- Book appointments with a selected therapist
- See real-time updates of available slots

## API Endpoints

### Create an available slot (for therapists)

```
POST /api/appointments/therapist/slots
```

**Request Body**:

```json
{
  "therapist_id": "123",
  "start_time": "2023-06-01T10:00:00",
  "end_time": "2023-06-01T11:00:00"
}
```

**Response**:

```json
{
  "success": true,
  "message": "Slot created successfully"
}
```

### Create availability range (for therapists)

```
POST /api/appointments/therapist/availability
```

**Request Body**:

```json
{
  "therapist_id": "123",
  "start_time": "2023-06-01T09:00:00",
  "end_time": "2023-06-01T17:00:00",
  "slot_duration_minutes": 60
}
```

**Response**:

```json
{
  "success": true,
  "message": "Created 8 slots successfully"
}
```

### List available slots (for clients)

```
GET /api/appointments/therapist/{therapist_id}/slots?date=2023-06-01
```

**Response**:

```json
{
  "success": true,
  "slots": [
    {
      "therapist_id": "123",
      "start_time": "2023-06-01T10:00:00",
      "end_time": "2023-06-01T11:00:00",
      "status": "free"
    },
    {
      "therapist_id": "123",
      "start_time": "2023-06-01T14:00:00",
      "end_time": "2023-06-01T15:00:00",
      "status": "free"
    }
  ]
}
```

### List therapists with availability statistics

```
GET /api/appointments/therapists?date=2023-06-01&therapist_ids=123,456
```

**Response**:

```json
{
  "success": true,
  "date": "2023-06-01",
  "therapists": [
    {
      "therapist_id": "123",
      "total_slots": 8,
      "available_slots": 6,
      "booked_slots": 2
    },
    {
      "therapist_id": "456",
      "total_slots": 5,
      "available_slots": 3,
      "booked_slots": 2
    }
  ]
}
```

### Book a slot (for clients)

```
POST /api/appointments/book
```

**Request Body**:

```json
{
  "therapist_id": "123",
  "slot_time": "2023-06-01T10:00:00"
}
```

**Response**:

```json
{
  "success": true,
  "message": "Slot booked successfully"
}
```

### Cancel a booking (for therapists)

```
POST /api/appointments/cancel
```

**Request Body**:

```json
{
  "therapist_id": "123",
  "slot_time": "2023-06-01T10:00:00"
}
```

**Response**:

```json
{
  "success": true,
  "message": "Booking canceled successfully"
}
```

## CLI Interface

The application also provides a CLI tool for interacting with the scheduling system directly from the command line.

### Usage

```bash
# Create a new time slot for a therapist
python cli.py create-slot <therapist_id> <start_time> <end_time>

# List available slots for a therapist on a specific date
python cli.py list-slots <therapist_id> <date>

# Book a slot with a therapist
python cli.py book-slot <therapist_id> <slot_time>

# Cancel a booked slot
python cli.py cancel-booking <therapist_id> <slot_time>
```

### Examples

```bash
# Create a new slot
python cli.py create-slot therapist123 "2023-06-01T10:00:00" "2023-06-01T11:00:00"

# List available slots
python cli.py list-slots therapist123 "2023-06-01"

# Book a slot
python cli.py book-slot therapist123 "2023-06-01T10:00:00"

# Cancel a booking
python cli.py cancel-booking therapist123 "2023-06-01T10:00:00"
```

## Data Storage

The application uses Firebase Realtime Database for data storage:

- Data is stored in the `appointments` node
- Each therapist's slots are stored under their ID
- Slots are stored as arrays of objects with start_time, end_time, and status

Example database structure:

```json
{
  "appointments": {
    "therapist_id_1": [
      {
        "start_time": "2023-06-01T10:00:00",
        "end_time": "2023-06-01T11:00:00",
        "status": "free"
      }
    ],
    "therapist_id_2": [
      {
        "start_time": "2023-06-01T14:00:00",
        "end_time": "2023-06-01T15:00:00",
        "status": "busy"
      }
    ]
  }
}
```

## Assumptions

1. All time slots are exactly 1 hour
2. A slot can only be in one of two states: "free" or "busy"
3. Times must be rounded to the hour (e.g., 10:00, not 10:30)
4. Therapist IDs are unique strings
5. For simplicity, no authentication/authorization is implemented
6. No notifications are sent to users when slots are booked/cancelled
