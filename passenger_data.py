from faker import Faker
import uuid
import random
from datetime import datetime, timedelta
import numpy as np
from fastavro import writer  

fake = Faker()

# Constants
CITY_CENTER = (40.7128, -74.0060)  # NYC coordinates
CITY_RADIUS = 0.1
RUSH_HOURS_MORNING = (7, 10)
RUSH_HOURS_EVENING = (16, 19)

# Global passenger pool for repeat customers
PASSENGER_POOL = set()

def generate_location(base_location=None, max_distance=0.05):
    """Generate a location, optionally based on another location"""
    if base_location:
        lat, lon = base_location['latitude'], base_location['longitude']
    else:
        lat, lon = CITY_CENTER
    
    new_lat = lat + np.random.normal(0, max_distance)
    new_lon = lon + np.random.normal(0, max_distance)
    return {'latitude': float(new_lat), 'longitude': float(new_lon)}

def get_passenger_id():
    """Get existing or create new passenger ID"""
    if PASSENGER_POOL and random.random() < 0.3:  # 30% chance of repeat customer
        return random.choice(list(PASSENGER_POOL))
    new_id = str(uuid.uuid4())[:8]
    PASSENGER_POOL.add(new_id)
    return new_id

def generate_fare_estimate(ride_type, duration_estimate):
    """Generate realistic fare based on duration and ride type"""
    base_rates = {
        'pool': 1.5,
        'standard': 2.0,
        'premium': 3.0
    }
    base_fare = (duration_estimate / 60) * base_rates[ride_type]  # per minute
    distance_fare = random.uniform(5, 20)  # random distance component
    return round(base_fare + distance_fare, 2)


def generate_feedback(rating):
    """Generate feedback based on rating"""
    if rating in [1, 2]:
        comment = random.choice([
            "Driver was late",
            "Car wasn't clean",
            "Driver took a longer route",
            "Poor service"
        ])
    elif rating == 5:
        comment = random.choice([
            "Great service!",
            "Very professional driver",
            "Clean car and smooth ride",
            "Excellent experience"
        ])
    else:
        # For ratings 3-4, provide a neutral comment instead of None
        comment = random.choice([
            "OK ride",
            "Normal trip",
            "Average experience",
            "Got me there"
        ])
    
    return {
        'rating': rating,
        'comments': comment  # Never return None for comments
    }
def generate_passenger_record(timestamp=None):
    """Generate a single passenger record"""
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())

    # Select ride type based on distribution
    ride_type = random.choices(
        ['standard', 'premium', 'pool'],
        weights=[0.7, 0.2, 0.1]
    )[0]

    # Generate locations
    pickup_location = generate_location()
    dropoff_location = generate_location(pickup_location)

    # Generate duration estimate (between 5 minutes and 2 hours)
    duration_estimate = random.randint(300, 7200)

    # Base record
    record = {
        'request_id': str(uuid.uuid4()),
        'passenger_id': get_passenger_id(),
        'timestamp': timestamp,
        'pickup_location': pickup_location,
        'dropoff_location': dropoff_location,
        'status': 'requested',
        'cancellation_reason': None,
        'driver_id': None,
        'ride_type': ride_type,
        'duration_estimate': duration_estimate,
        'fare_estimate': generate_fare_estimate(ride_type, duration_estimate),
        'feedback': None
    }

    # Determine ride outcome
    outcome_chance = random.random()
    if outcome_chance < 0.7:  # 70% completed rides
        record['status'] = 'completed'
        record['driver_id'] = str(uuid.uuid4())[:8]
        
        # Add feedback for some completed rides
        if random.random() < 0.4:  # 40% chance of feedback
            rating = random.choices(
                [1, 2, 3, 4, 5],
                weights=[0.05, 0.05, 0.1, 0.3, 0.5]
            )[0]
            record['feedback'] = generate_feedback(rating)
            
    elif outcome_chance < 0.85:  # 15% cancelled by passenger
        record['status'] = 'canceled'
        record['cancellation_reason'] = random.choice([
            "Changed plans",
            "Wait time too long",
            "Booked by mistake",
            "Found alternative transport"
        ])
    else:  # 15% cancelled by system/timeout
        record['status'] = 'canceled'
        record['cancellation_reason'] = "No drivers available"

    return record

def generate_records(num_records):
    """Generate multiple passenger records"""
    records = []
    base_time = int(datetime.now().timestamp())
    
    for _ in range(num_records):
        # Generate timestamp with more requests during rush hours
        time_offset = random.randint(-86400, 86400)  # ±1 day
        timestamp = base_time + time_offset
        
        record = generate_passenger_record(timestamp)
        records.append(record)
    
    return records

# Generate and save records



def save_records_to_avro(num_records, output_file='passenger_events.avro'):
    """Generate records and save them to an Avro file"""
    records = generate_records(num_records)
    
    from fastavro import writer
    with open(output_file, 'wb') as out:
        writer(out, parsed_passenger_schema, records)
    
    return records

# Example usage:
# Generate 1000 records
records = save_records_to_avro(1000)

# Print a sample record
print("Sample Passenger Record:")
print(records[0])