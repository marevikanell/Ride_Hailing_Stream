#-----------------------------

# NOT WORKING, JUST TOOK NEALS CODE AND ADDED SOME MORE CONSTRAINTS AND INTERDEPENDENCE BETWEEN THE 2 SCHEMAS!

#-----------------------------
import json
import random
import uuid
from datetime import datetime
from faker import Faker
from fastavro import writer
import math

from driver_avail_schema import parsed_driver_schema
from passenger_schema import parsed_passenger_schema

fake = Faker()

# Define realistic constraints
CITY_CENTER = (40.7128, -74.0060)  # Example: NYC coordinates
CITY_RADIUS = 0.1  # Approximately 11km radius
RUSH_HOURS_MORNING = (7, 10)  # 7 AM - 10 AM
RUSH_HOURS_EVENING = (16, 19)  # 4 PM - 7 PM

# Vehicle distribution
VEHICLE_DISTRIBUTION = {
    'sedan': 0.65,
    'suv': 0.20,
    'hatchback': 0.10,
    'van': 0.03,
    'truck': 0.02
}

# Traffic condition weights
TRAFFIC_WEIGHTS_RUSH = [0.4, 0.3, 0.2, 0.1]  # heavy, gridlock, moderate, light
TRAFFIC_WEIGHTS_NORMAL = [0.4, 0.3, 0.15, 0.05, 0.1]  # light, moderate, heavy, gridlock, unknown

# Helper functions
def random_location_near_city():
    """Generate a random location within CITY_RADIUS of CITY_CENTER."""
    lat, lon = CITY_CENTER
    delta_lat = random.uniform(-CITY_RADIUS, CITY_RADIUS)
    delta_lon = random.uniform(-CITY_RADIUS, CITY_RADIUS)
    return {"latitude": lat + delta_lat, "longitude": lon + delta_lon}

def haversine_distance(loc1, loc2):
    """Calculate the great-circle distance between two points."""
    lat1, lon1 = loc1["latitude"], loc1["longitude"]
    lat2, lon2 = loc2["latitude"], loc2["longitude"]
    R = 6371  # Radius of the Earth in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_traffic_condition(timestamp):
    """Determine traffic condition based on time of day."""
    hour = datetime.fromtimestamp(timestamp).hour
    is_rush_hour = RUSH_HOURS_MORNING[0] <= hour <= RUSH_HOURS_MORNING[1] or \
                   RUSH_HOURS_EVENING[0] <= hour <= RUSH_HOURS_EVENING[1]
    weights = TRAFFIC_WEIGHTS_RUSH if is_rush_hour else TRAFFIC_WEIGHTS_NORMAL
    return random.choices(['heavy', 'gridlock', 'moderate', 'light', 'unknown'], weights=weights)[0]

def get_driver_status(hour):
    """Determine likely driver status based on time."""
    if RUSH_HOURS_MORNING[0] <= hour <= RUSH_HOURS_MORNING[1] or \
       RUSH_HOURS_EVENING[0] <= hour <= RUSH_HOURS_EVENING[1]:
        return random.choices(['available', 'en_route', 'engaged', 'offline'], weights=[0.15, 0.35, 0.45, 0.05])[0]
    elif 0 <= hour <= 5:
        return random.choices(['available', 'en_route', 'engaged', 'offline'], weights=[0.1, 0.1, 0.2, 0.6])[0]
    else:
        return random.choices(['available', 'en_route', 'engaged', 'offline'], weights=[0.3, 0.3, 0.3, 0.1])[0]


def estimate_duration(distance_km, traffic_condition):
    """Estimate ride duration based on distance and traffic condition."""
    base_speed_kmph = {
        'light': 50,
        'moderate': 30,
        'heavy': 20,
        'gridlock': 10,
        'unknown': 25
    }
    speed = base_speed_kmph.get(traffic_condition, 25)  # Default to 25 km/h
    return int((distance_km / speed) * 3600)  # Return duration in seconds


def estimate_fare(distance_km, ride_type, traffic_condition):
    """Estimate fare based on distance, ride type, and traffic conditions."""
    base_rate = {'standard': 1.0, 'premium': 1.5, 'pool': 0.8}
    traffic_multiplier = {'light': 1.0, 'moderate': 1.2, 'heavy': 1.5, 'gridlock': 1.8, 'unknown': 1.1}
    rate = base_rate[ride_type] * traffic_multiplier.get(traffic_condition, 1.0)
    return round(rate * distance_km * 10, 2)  # Base fare calculation


def generate_driver_event(driver_id, ride_id=None, timestamp=None):
    """Generate a driver event with realistic constraints."""
    timestamp = timestamp or fake.unix_time()
    return {
        "event_id": str(uuid.uuid4()),
        "driver_id": driver_id,
        "timestamp": timestamp,
        "location": random_location_near_city(),
        "status": get_driver_status(datetime.fromtimestamp(timestamp).hour),
        "ride_id": ride_id,
        "vehicle_type": random.choices(list(VEHICLE_DISTRIBUTION.keys()), weights=VEHICLE_DISTRIBUTION.values())[0],
        "driver_session_id": str(uuid.uuid4()),
        "traffic_condition": get_traffic_condition(timestamp)
    }


def generate_passenger_request(driver_id=None, status="requested", ride_id=None, timestamp=None):
    """Generate a passenger request with realistic constraints."""
    timestamp = timestamp or fake.unix_time()
    pickup = random_location_near_city()
    dropoff = random_location_near_city()
    distance_km = haversine_distance(pickup, dropoff)
    traffic_condition = get_traffic_condition(timestamp)
    duration_estimate = estimate_duration(distance_km, traffic_condition)
    ride_type = random.choice(['standard', 'premium', 'pool'])
    fare_estimate = estimate_fare(distance_km, ride_type, traffic_condition)

    return {
        "request_id": str(uuid.uuid4()),
        "passenger_id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "pickup_location": pickup,
        "dropoff_location": dropoff,
        "status": status,
        "cancellation_reason": None if status != "canceled" else fake.sentence(),
        "driver_id": driver_id,
        "ride_type": ride_type,
        "duration_estimate": duration_estimate,
        "fare_estimate": fare_estimate,
        "feedback": None if status != "completed" else {
            "rating": random.randint(1, 5),
            "comments": fake.sentence()
        }
    }


def generate_matched_data(num_records):
    """Generate matched driver and passenger data."""
    driver_data, passenger_data = [], []

    for _ in range(num_records):
        ride_id = str(uuid.uuid4())
        timestamp = fake.unix_time()

        driver_id = str(uuid.uuid4())
        driver_event = generate_driver_event(driver_id=driver_id, ride_id=ride_id, timestamp=timestamp)
        driver_data.append(driver_event)

        passenger_request = generate_passenger_request(driver_id=driver_id, status="accepted", ride_id=ride_id, timestamp=timestamp)
        passenger_data.append(passenger_request)

    return driver_data, passenger_data


# Generate and save data
def save_data(num_records, json_file_driver, avro_file_driver, json_file_passenger, avro_file_passenger):
    driver_data, passenger_data = generate_matched_data(num_records)

    # Save driver data
    with open(json_file_driver, 'w') as f:
        json.dump(driver_data, f, indent=4)
    with open(avro_file_driver, 'wb') as f:
        writer(f, parsed_driver_schema, driver_data)

    # Save passenger data
    with open(json_file_passenger, 'w') as f:
        json.dump(passenger_data, f, indent=4)
    with open(avro_file_passenger, 'wb') as f:
        writer(f, parsed_passenger_schema, passenger_data)


# Generate 100 matched records
save_data(100, 'drivers.json', 'drivers.avro', 'passenger_requests.json', 'passenger_requests.avro')

print("Data generation complete with advanced constraints!")

