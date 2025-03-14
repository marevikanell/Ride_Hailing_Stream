import json
import random
import uuid
import time
from datetime import datetime, timedelta
from faker import Faker
from fastavro import writer
import math

from driver_avail_schema import parsed_driver_schema
from passenger_schema import parsed_passenger_schema

fake = Faker()

CITY_CENTER = (40.7128, -74.0060)
CITY_RADIUS = 0.1
RUSH_HOURS = [(7, 10), (16, 19)]

VEHICLE_DISTRIBUTION = {
    'sedan': 0.65,
    'suv': 0.20,
    'hatchback': 0.10,
    'van': 0.03,
    'truck': 0.02
}

TRAFFIC_WEIGHTS_RUSH = [0.4, 0.3, 0.2, 0.1, 0.0]
TRAFFIC_WEIGHTS_NORMAL = [0.4, 0.3, 0.15, 0.05, 0.1]

def random_location_near_city():
    lat, lon = CITY_CENTER
    delta_lat = random.uniform(-CITY_RADIUS, CITY_RADIUS)
    delta_lon = random.uniform(-CITY_RADIUS, CITY_RADIUS)
    return {"latitude": lat + delta_lat, "longitude": lon + delta_lon}

def haversine_distance(loc1, loc2):
    lat1, lon1 = loc1["latitude"], loc1["longitude"]
    lat2, lon2 = loc2["latitude"], loc2["longitude"]
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_traffic_condition(timestamp):
    hour = datetime.fromtimestamp(timestamp).hour
    is_rush_hour = any(start <= hour <= end for start, end in RUSH_HOURS)
    weights = TRAFFIC_WEIGHTS_RUSH if is_rush_hour else TRAFFIC_WEIGHTS_NORMAL
    return random.choices(['heavy', 'gridlock', 'moderate', 'light', 'unknown'], weights=weights, k=1)[0]

def estimate_duration(distance_km, traffic_condition):
    base_speed_kmph = {'light': 50, 'moderate': 30, 'heavy': 20, 'gridlock': 10, 'unknown': 25}
    speed = base_speed_kmph.get(traffic_condition, 25)
    return int((distance_km / speed) * 3600)

def estimate_fare(distance_km, ride_type, traffic_condition):
    base_rate = {'standard': 1.0, 'premium': 1.5, 'pool': 0.8}
    traffic_multiplier = {'light': 1.0, 'moderate': 1.2, 'heavy': 1.5, 'gridlock': 1.8, 'unknown': 1.1}
    rate = base_rate[ride_type] * traffic_multiplier.get(traffic_condition, 1.0)
    return round(rate * distance_km * 10, 2)

def generate_driver_event(driver_id, ride_id=None, timestamp=None):
    timestamp = timestamp or int(datetime.utcnow().timestamp())
    event = {
        "event_id": str(uuid.uuid4()),
        "driver_id": driver_id,
        "timestamp": timestamp,
        "location": random_location_near_city(),
        "status": "available" if ride_id is None else "engaged",
        "ride_id": ride_id,
        "vehicle_type": random.choices(list(VEHICLE_DISTRIBUTION.keys()), weights=VEHICLE_DISTRIBUTION.values())[0],
        "driver_session_id": str(uuid.uuid4()),
        "traffic_condition": get_traffic_condition(timestamp)
    }
    print(f"Driver Event Created: {event}")
    return event

def generate_passenger_request(driver_id=None, status="requested", ride_id=None, timestamp=None):
    timestamp = timestamp or int(datetime.utcnow().timestamp())
    pickup = random_location_near_city()
    dropoff = random_location_near_city()
    distance_km = haversine_distance(pickup, dropoff)
    traffic_condition = get_traffic_condition(timestamp)
    duration_estimate = estimate_duration(distance_km, traffic_condition)
    ride_type = random.choice(['standard', 'premium', 'pool'])
    fare_estimate = estimate_fare(distance_km, ride_type, traffic_condition)
    event = {
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
    print(f"Passenger Request Created: {event}")
    return event

def save_data(num_records):
    print("Starting simulation...")
    driver_data, passenger_data = [], []
    for _ in range(num_records):
        ride_id = str(uuid.uuid4())
        timestamp = int(datetime.utcnow().timestamp())
        driver_id = str(uuid.uuid4())
        driver_event = generate_driver_event(driver_id=driver_id, ride_id=ride_id, timestamp=timestamp)
        driver_data.append(driver_event)
        passenger_request = generate_passenger_request(driver_id=driver_id, status="accepted", ride_id=ride_id, timestamp=timestamp)
        passenger_data.append(passenger_request)
        print(f"Driver {driver_id} is now delivering passenger {passenger_request['passenger_id']}...")
        time.sleep(random.uniform(2, 5))
        print(f"Ride completed for passenger {passenger_request['passenger_id']}")
    print("Simulation complete. Saving data...")
    with open('drivers.json', 'w') as f:
        json.dump(driver_data, f, indent=4)
    with open('drivers.avro', 'wb') as f:
        writer(f, parsed_driver_schema, driver_data)
    with open('passenger_requests.json', 'w') as f:
        json.dump(passenger_data, f, indent=4)
    with open('passenger_requests.avro', 'wb') as f:
        writer(f, parsed_passenger_schema, passenger_data)
    print("Data generation and saving complete!")

save_data(100)
