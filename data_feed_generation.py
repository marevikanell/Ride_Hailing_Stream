import json
import uuid
from datetime import datetime
from faker import Faker
from fastavro import writer
import math
import random
from driver_avail_schema import parsed_driver_schema
from passenger_schema import parsed_passenger_schema

fake = Faker()

# Define realistic constraints
CITY_CENTER = (40.7128, -74.0060)  # NYC coordinates
CITY_RADIUS = 0.03  # Reduced to ~3.3 km for realistic trips
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
TRAFFIC_WEIGHTS_RUSH = [0.4, 0.3, 0.2, 0.1]  # Matches "heavy", "gridlock", "moderate", "light"
TRAFFIC_WEIGHTS_NORMAL = [0.4, 0.3, 0.15, 0.05, 0.1]

# Global counters for IDs
passenger_id_counter = 0
driver_id_counter = 0
ride_id_counter = 0
event_id_counter = 0

def generate_id(prefix, counter):
    """Generate a formatted ID with a prefix and a counter."""
    return f"{prefix}{counter:06d}"

def random_location_near_city():
    """Generate a random location within CITY_RADIUS of CITY_CENTER."""
    lat, lon = CITY_CENTER
    delta_lat = fake.pyfloat(min_value=-CITY_RADIUS, max_value=CITY_RADIUS)
    delta_lon = fake.pyfloat(min_value=-CITY_RADIUS, max_value=CITY_RADIUS)
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
    traffic_conditions = ["heavy", "gridlock", "moderate", "light", "unknown"]

    # Adjust traffic conditions for rush hour
    if is_rush_hour:
        traffic_conditions = traffic_conditions[:len(weights)]

    if len(weights) != len(traffic_conditions):
        raise ValueError("Weights and traffic conditions lengths do not match.")

    return random.choices(traffic_conditions, weights=weights, k=1)[0]

def get_driver_status(hour):
    """Determine likely driver status based on time."""
    if RUSH_HOURS_MORNING[0] <= hour <= RUSH_HOURS_MORNING[1] or \
       RUSH_HOURS_EVENING[0] <= hour <= RUSH_HOURS_EVENING[1]:
        statuses = ['available', 'en_route', 'engaged', 'offline']
        weights = [0.15, 0.35, 0.45, 0.05]
    elif 0 <= hour <= 5:
        statuses = ['available', 'en_route', 'engaged', 'offline']
        weights = [0.1, 0.1, 0.2, 0.6]
    else:
        statuses = ['available', 'en_route', 'engaged', 'offline']
        weights = [0.3, 0.3, 0.3, 0.1]

    if len(weights) != len(statuses):
        raise ValueError("Weights and statuses lengths do not match.")

    return random.choices(statuses, weights=weights, k=1)[0]

def estimate_duration(distance_km, traffic_condition):
    """Estimate ride duration based on distance and traffic condition."""
    base_speed_kmph = {
        "light": 50,
        "moderate": 30,
        "heavy": 20,
        "gridlock": 10,
        "unknown": 25
    }
    speed = base_speed_kmph.get(traffic_condition, 25)  # Default to 25 km/h
    return max(1, min(int((distance_km / speed) * 60), 90))  

def estimate_fare(distance_km, ride_type, traffic_condition):
    """Estimate fare based on distance, ride type, and traffic conditions."""
    base_rate = {"standard": 1.0, "premium": 1.5, "pool": 0.8}
    traffic_multiplier = {"light": 1.0, "moderate": 1.2, "heavy": 1.5, "gridlock": 1.8, "unknown": 1.1}
    rate = base_rate[ride_type] * traffic_multiplier.get(traffic_condition, 1.0)
    fare = max(5, round(rate * distance_km * 8, 2))
    return min(fare, 100)  # capped fare at $100

def generate_cancellation_reason():
    """Generate a realistic cancellation reason using Faker and predefined templates."""
    templates = [
        "Driver delayed due to {reason}.",
        "Passenger unable to find the driver at {location}.",
        "Ride request canceled because {issue}.",
        "Unexpected personal emergency occurred {time}.",
        "Driver's vehicle broke down near {location}.",
        "Driver refused to pick up due to {reason}.",
        "Passenger found an alternative ride {time}.",
        "Destination changed by the passenger at the last minute.",
        "Driver reported a safety concern at {location}.",
        "Passenger did not show up at the pickup location {time}."
    ]
    
    # Dynamic components generated by Faker
    faker_context = {
        "reason": fake.catch_phrase(),
        "location": fake.street_name(),
        "issue": fake.bs(),
        "time": fake.time()
    }
    
    # Select a template and substitute placeholders dynamically
    template = random.choice(templates)
    return template.format(**faker_context)

def generate_feedback_comments(rating):
    """Generate realistic feedback comments based on the rating."""
    positive_comments = [
        "The ride was very smooth and comfortable.",
        "Driver was polite and the vehicle was clean.",
        "Arrived on time and provided great service.",
        "Very professional and courteous driver.",
        "Enjoyed the ride, no complaints at all."
    ]

    neutral_comments = [
        "The ride was okay, nothing special.",
        "Driver followed the route, but the experience was average.",
        "Had to wait a bit longer than expected, but it was fine.",
        "Ride was acceptable, though the car could have been cleaner.",
        "Service was decent, but there’s room for improvement."
    ]

    negative_comments = [
        "Driver was late and the vehicle was not clean.",
        "Had a very uncomfortable ride due to traffic and delays.",
        "Driver was rude and took an unnecessary detour.",
        "The car condition was poor and the experience was bad.",
        "Not satisfied with the service, would not recommend."
    ]

    if rating >= 4:
        return random.choice(positive_comments)
    elif rating == 3:
        return random.choice(neutral_comments)
    else:
        return random.choice(negative_comments)

def generate_driver_event(driver_id, ride_id=None, timestamp=None):
    global event_id_counter
    event_id = generate_id("E", event_id_counter)
    event_id_counter += 1
    timestamp = timestamp or fake.unix_time()
    return {
        "event_id": event_id,
        "driver_id": driver_id,
        "timestamp": timestamp,
        "location": random_location_near_city(),
        "status": get_driver_status(datetime.fromtimestamp(timestamp).hour),
        "ride_id": ride_id,
        "vehicle_type": random.choices(list(VEHICLE_DISTRIBUTION.keys()),
                                       weights=list(VEHICLE_DISTRIBUTION.values()), k=1)[0],
        "driver_session_id": generate_id("S", int(driver_id[-6:])),  # Ensure the session ID corresponds to the driver ID # Ensure unique session for each driver
        "traffic_condition": get_traffic_condition(timestamp)
    }

def generate_passenger_request(driver_id=None, status="requested", ride_id=None, timestamp=None):
    """Generate a passenger request with realistic constraints."""
    global passenger_id_counter, ride_id_counter
    passenger_id = generate_id("P", passenger_id_counter)
    passenger_id_counter += 1

    ride_id = ride_id or generate_id("R", ride_id_counter)
    ride_id_counter += 1
    timestamp = timestamp or fake.unix_time()
    pickup = random_location_near_city()
    dropoff = random_location_near_city()
    distance_km = haversine_distance(pickup, dropoff) # Cap distance at 50 km
    traffic_condition = get_traffic_condition(timestamp)
    duration_estimate = estimate_duration(distance_km, traffic_condition)
    ride_type = random.choice(["standard", "premium", "pool"])
    fare_estimate = estimate_fare(distance_km, ride_type, traffic_condition) # Cap fare at $200

    return {
        "request_id": generate_id("REQ", passenger_id_counter),
        "passenger_id": passenger_id,
        "timestamp": timestamp,
        "pickup_location": pickup,
        "dropoff_location": dropoff,
        "status": status,
        "cancellation_reason": None if status != "canceled" else generate_cancellation_reason(),
        "driver_id": driver_id,
        "ride_type": ride_type,
        "duration_estimate": duration_estimate,
        "fare_estimate": fare_estimate,
        "feedback": None if status != "completed" else {
        "rating": fake.random_int(min=1, max=5),
        "comments": generate_feedback_comments(fake.random_int(min=1, max=5))
             }
    }
    
def match_requests_to_drivers(driver_data, passenger_requests):
    """
    Match passenger requests to drivers and update statuses accordingly.

    Args:
        driver_data (list): List of driver events.
        passenger_requests (list): List of passenger requests.

    Returns:
        list: Updated passenger requests with matching drivers.
        list: Updated driver data with corresponding statuses.
    """
    matched_requests = []
    available_drivers = [driver for driver in driver_data if driver["status"] == "available"]
    driver_index = 0  # Initialize driver index for round-robin allocation

    for request in passenger_requests:
        if request["status"] == "requested" and available_drivers:
            # Match with the next available driver in a round-robin manner
            driver = available_drivers[driver_index]
            driver_index = (driver_index + 1) % len(available_drivers)  # Move to the next driver

            # Update request
            request["driver_id"] = driver["driver_id"]
            request["status"] = "accepted"

            # Update driver status to engaged
            driver["status"] = "engaged"

            # Simulate potential completion or cancellation of the ride
            if random.random() > 0.2:  # 80% chance of ride completion
                request["status"] = "completed"
                rating = fake.random_int(min=3, max=5)  # Generate rating in the range 3 to 5
                request["feedback"] = {
                    "rating": rating,
                    "comments": generate_feedback_comments(rating)  # Generate realistic feedback based on rating
                }
                driver["status"] = "available"  # Driver becomes available again
            else:  # 20% chance of cancellation
                request["status"] = "canceled"
                request["cancellation_reason"] = generate_cancellation_reason()
                driver["status"] = "available"  # Driver becomes available again

        matched_requests.append(request)

    return matched_requests, driver_data

# Advanced save_data function with matching
def save_data_with_matching(num_drivers, num_requests, json_file_driver, avro_file_driver, json_file_passenger, avro_file_passenger):
    """
    Generate data with realistic driver and passenger interactions and save it to files.
    
    Args:
        num_drivers (int): Number of drivers.
        num_requests (int): Number of passenger requests.
        json_file_driver (str): Output JSON file for driver data.
        avro_file_driver (str): Output Avro file for driver data.
        json_file_passenger (str): Output JSON file for passenger data.
        avro_file_passenger (str): Output Avro file for passenger data.
    """
    driver_data = []
    passenger_data = []
    global driver_id_counter

    # Generate drivers
    for _ in range(num_drivers):
        driver_id = generate_id("D", driver_id_counter)
        driver_id_counter += 1
        driver_data.append(generate_driver_event(driver_id))

    # Generate passenger requests
    for _ in range(num_requests):
        passenger_data.append(generate_passenger_request())

    # Match requests to drivers
    passenger_data, driver_data = match_requests_to_drivers(driver_data, passenger_data)

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

# Generate and save data with matching
save_data_with_matching(5000, 10000, 'drivers.json', 'drivers.avro', 'passenger_requests.json', 'passenger_requests.avro')

print("Data generation with matching complete!")
