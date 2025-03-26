# Therapist-Client Scheduling System

A Flask-based API for managing therapist-client appointments.

## Features

- Therapists can post available 1-hour slots
- Clients can view available slots by therapist and date
- Clients can book available slots with a specific therapist
- Double bookings are prevented
- Clients can cancel existing appointments
- Interfaces via REST API and CLI
- Firebase Realtime Database integration

## Tech Stack

- Python 3.8+
- Flask (Web framework)
- Pydantic (Data validation and settings management)
- Firebase Admin SDK (Database)

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
   - Select your project "sansa-sswe-kevin"
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

### Cancel a booking (for clients)

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
