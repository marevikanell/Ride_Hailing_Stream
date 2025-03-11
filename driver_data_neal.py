from faker import Faker
import uuid
import time
import random
from datetime import datetime, timedelta
import numpy as np
from driver_avail_schema import parsed_driver_schema

fake = Faker()

# Define realistic constraints
CITY_CENTER = (40.7128, -74.0060)  # Example: NYC coordinates
CITY_RADIUS = 0.1  # Approximately 11km radius
RUSH_HOURS_MORNING = (7, 10)  # 7 AM - 10 AM
RUSH_HOURS_EVENING = (16, 19)  # 4 PM - 7 PM

# Vehicle distribution based on typical fleet composition
VEHICLE_DISTRIBUTION = {
    'sedan': 0.65,  # 65% of fleet
    'suv': 0.20,
    'hatchback': 0.10,
    'van': 0.03,
    'truck': 0.02
}

def generate_realistic_location(center, radius):
    """Generate location with higher density near city center"""
    # Use normal distribution for more realistic clustering
    lat = center[0] + np.random.normal(0, radius/2)
    lng = center[1] + np.random.normal(0, radius/2)
    return {'latitude': float(lat), 'longitude': float(lng)}

def get_traffic_condition(timestamp):
    """Determine traffic condition based on time of day"""
    hour = datetime.fromtimestamp(timestamp).hour
    
    # Rush hour logic
    is_rush_hour = (RUSH_HOURS_MORNING[0] <= hour <= RUSH_HOURS_MORNING[1] or 
                   RUSH_HOURS_EVENING[0] <= hour <= RUSH_HOURS_EVENING[1])
    
    if is_rush_hour:
        # During rush hours, higher chance of heavy traffic
        return random.choices(
            ['heavy', 'gridlock', 'moderate', 'light'],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
    else:
        # Normal hours, lighter traffic
        return random.choices(
            ['light', 'moderate', 'heavy', 'gridlock', 'unknown'],
            weights=[0.4, 0.3, 0.15, 0.05, 0.1]
        )[0]

def get_driver_status(hour):
    """Determine likely driver status based on time"""
    if RUSH_HOURS_MORNING[0] <= hour <= RUSH_HOURS_MORNING[1] or \
       RUSH_HOURS_EVENING[0] <= hour <= RUSH_HOURS_EVENING[1]:
        # During rush hours, more likely to be engaged
        return random.choices(
            ['available', 'en_route', 'engaged', 'offline'],
            weights=[0.15, 0.35, 0.45, 0.05]
        )[0]
    elif 0 <= hour <= 5:  # Late night
        # Late night, more likely to be offline
        return random.choices(
            ['available', 'en_route', 'engaged', 'offline'],
            weights=[0.1, 0.1, 0.2, 0.6]
        )[0]
    else:
        # Normal hours
        return random.choices(
            ['available', 'en_route', 'engaged', 'offline'],
            weights=[0.3, 0.3, 0.3, 0.1]
        )[0]

def generate_driver_event(timestamp=None):
    """Generate a more realistic driver event"""
    if timestamp is None:
        timestamp = int(time.time())
    
    current_hour = datetime.fromtimestamp(timestamp).hour
    status = get_driver_status(current_hour)
    
    # Select vehicle type based on realistic distribution
    vehicle_type = random.choices(
        list(VEHICLE_DISTRIBUTION.keys()),
        weights=list(VEHICLE_DISTRIBUTION.values())
    )[0]
    
    return {
        'event_id': str(uuid.uuid4()),
        'driver_id': str(uuid.uuid4())[:8],
        'timestamp': timestamp,
        'location': generate_realistic_location(CITY_CENTER, CITY_RADIUS),
        'status': status,
        'ride_id': str(uuid.uuid4()) if status in ['en_route', 'engaged'] else None,
        'vehicle_type': vehicle_type,
        'driver_session_id': str(uuid.uuid4()),
        'traffic_condition': get_traffic_condition(timestamp)
    }

def generate_1000_records():
    """Generate 1000 records with realistic time distribution"""
    events = []
    
    # Create a 24-hour time distribution with more events during rush hours
    # This will determine how many events to generate for each hour
    hourly_distribution = []
    for hour in range(24):
        if RUSH_HOURS_MORNING[0] <= hour <= RUSH_HOURS_MORNING[1] or \
           RUSH_HOURS_EVENING[0] <= hour <= RUSH_HOURS_EVENING[1]:
            # Rush hours get more weight
            hourly_distribution.extend([hour] * 8)
        elif 0 <= hour <= 5:
            # Late night gets less weight
            hourly_distribution.extend([hour] * 2)
        else:
            # Normal hours
            hourly_distribution.extend([hour] * 4)
    
    # Base date (today)
    base_date = datetime.now().date()
    
    # Generate 1000 events
    for _ in range(1000):
        # Pick a random hour based on our distribution
        hour = random.choice(hourly_distribution)
        
        # Generate a random minute and second
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        # Create timestamp
        event_time = datetime.combine(base_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute, seconds=second)
        timestamp = int(event_time.timestamp())
        
        # Generate and add the event
        events.append(generate_driver_event(timestamp))
    
    return events

# Generate 1000 records
sample_events = generate_1000_records()

# Print a few sample events
for event in sample_events[:5]:
    print(event)
print(f"\nTotal events generated: {len(sample_events)}")

# Optional: Sort events by timestamp to see them in chronological order
sorted_events = sorted(sample_events, key=lambda x: x['timestamp'])



from fastavro import writer, parse_schema
import os



def write_to_avro_file(records, file_path):
    """Write records to an Avro file."""
    with open(file_path, 'wb') as out:
        writer(out, parsed_driver_schema, records) # loaded from the driver_avail_schema script

# Generate 1000 records
sample_events = generate_1000_records()


# Write the records to an Avro file
avro_file_path = 'driver_events.avro'
write_to_avro_file(sample_events, avro_file_path)

print(f"Records have been written to {avro_file_path}")


with open('driver_events.avro', 'rb') as out:
    schema_plus_record=out.read()

schema_plus_record[:1000]