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

CITY_CENTER = (40.7128, -74.0060)  # NYC coordinates
CITY_RADIUS = 0.03  # Reduced to ~3.3 km for realistic trips
RUSH_HOURS_MORNING = (7, 10)  # 7 AM - 10 AM
RUSH_HOURS_EVENING = (16, 19)  # 4 PM - 7 PM

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
    angle = random.uniform(0, 2 * math.pi)
    radius = CITY_RADIUS * math.sqrt(random.uniform(0, 1))
    delta_lat = radius * math.cos(angle) / 111  # convert km to degrees
    delta_lon = radius * math.sin(angle) / (111 * math.cos(math.radians(lat)))  # adjust for latitude
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

    TRAFFIC_WEIGHTS_RUSH = [0.4, 0.3, 0.2, 0.1, 0.0]

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
    base_speed_kmph = {'light': 50, 'moderate': 30, 'heavy': 15, 'gridlock': 5, 'unknown': 25}
    speed = base_speed_kmph.get(traffic_condition, 25)
    return max(1, min(int((distance_km / speed) * 60), 90))  # Convert to minutes, cap at 90 mins

def estimate_fare(distance_km, ride_type, traffic_condition):
    """Estimate fare with a base fare and capped max."""
    base_rate = {'standard': 1.0, 'premium': 1.5, 'pool': 0.8}
    traffic_multiplier = {'light': 1.0, 'moderate': 1.2, 'heavy': 1.5, 'gridlock': 2.0, 'unknown': 1.1}
    rate = base_rate[ride_type] * traffic_multiplier.get(traffic_condition, 1.0)
    fare = max(5, round(rate * distance_km * 8, 2))
    return min(fare, 100)  # capped fare at $100

def generate_driver_event(driver_id, driver_session_id, ride_id=None, timestamp=None):
    """Generate a driver event with realistic constraints."""
    timestamp = timestamp or fake.unix_time()
    return {
        "event_id": str(uuid.uuid4()),
        "driver_id": driver_id,
        "driver_session_id": driver_session_id,
        "timestamp": timestamp,
        "location": random_location_near_city(),
        "status": get_driver_status(datetime.fromtimestamp(timestamp).hour),
        "ride_id": ride_id,
        "vehicle_type": random.choices(list(VEHICLE_DISTRIBUTION.keys()), weights=VEHICLE_DISTRIBUTION.values())[0],
        "traffic_condition": get_traffic_condition(timestamp)
    }

def generate_passenger_request(driver_id, status="requested", ride_id=None, timestamp=None):
    """Generate a passenger request with realistic constraints."""
    timestamp = timestamp or fake.unix_time()
    pickup, dropoff = random_location_near_city(), random_location_near_city()
    distance_km = haversine_distance(pickup, dropoff)
    traffic_condition = get_traffic_condition(timestamp)
    return {
        "request_id": str(uuid.uuid4()),
        "passenger_id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "pickup_location": pickup,
        "dropoff_location": dropoff,
        "status": status,
        "driver_id": driver_id,
        "ride_type": random.choice(['standard', 'premium', 'pool']),
        "duration_estimate": estimate_duration(distance_km, traffic_condition),
        "fare_estimate": estimate_fare(distance_km, 'standard', traffic_condition)
    }

def generate_matched_data(num_records):
    """Generate matched driver and passenger data with shared drivers."""
    driver_data, passenger_data = [], []
    driver_dict = {}

    for _ in range(num_records):
        ride_id = str(uuid.uuid4())
        timestamp = fake.unix_time()

# each driver gets a session id when created &
        # if the driver is reused, the same session ID is retrieved from driver_dict.
        # passed to generate_driver_event() --> receives driver_session_id and includes it in the generated driver event.
        #Inside generate_driver_event(), driver_session_id is included:

        if random.random() > 0.5 and driver_dict:    # reuses driver
            driver_id, driver_session_id = random.choice(list(driver_dict.items()))
        else:
            driver_id, driver_session_id = str(uuid.uuid4()), str(uuid.uuid4())  # creates new driver
            driver_dict[driver_id] = driver_session_id

        driver_data.append(generate_driver_event(driver_id, driver_session_id, ride_id, timestamp))
        passenger_data.append(generate_passenger_request(driver_id, "accepted", ride_id, timestamp))

    return driver_data, passenger_data

def save_data(num_records, json_file_driver, avro_file_driver, json_file_passenger, avro_file_passenger):
    driver_data, passenger_data = generate_matched_data(num_records)
    json.dump(driver_data, open(json_file_driver, 'w'), indent=4)
    json.dump(passenger_data, open(json_file_passenger, 'w'), indent=4)

save_data(100, 'drivers.json', 'drivers.avro', 'passenger_requests.json', 'passenger_requests.avro')
print("Data generation complete!")


