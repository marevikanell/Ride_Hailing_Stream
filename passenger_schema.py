from fastavro import writer, reader, parse_schema
import io


passenger_request_schema = {
    'doc': 'A passenger request schema.',
    'name': 'Passenger Request',
    'namespace': 'stream.ride.information',
    'type': 'record',
    'fields': [
        {'name': 'request_id', 'type': 'string'},
        {'name': 'passenger_id', 'type': 'string'},
        {'name': 'timestamp', 'type': 'long', 'doc':'Time of status update: request, accepted, completed.'},
        {
            'name': 'pickup_location',
            'type': {
                'type': 'record',
                'name': 'Location',
                'fields': [
                    {'name': 'latitude', 'type': 'float'},
                    {'name': 'longitude', 'type': 'float'}
                ]
            }
        },
        {
            'name': 'dropoff_location',
            'type': 'Location'
        },
        {
            'name': 'status',
            'type': {
                'type': 'enum',
                'name': 'Status',
                'symbols': ['requested', 'accepted', 'canceled', 'completed']
            },
            'doc': 'Status of the request.'
        },
        {'name': 'cancellation_reason', 'type': ['null', 'string'], 'default': None},
        
        {'name': 'driver_id', 'type': ['null', 'string'], 'default': None},
        {
            'name': 'ride_type',
            'type': {
                'type': 'enum',
                'name': 'RideType',
                'symbols': ['standard', 'premium', 'pool']
            },
            'doc': 'Type of ride requested.'
        },
        {'name': 'duration_estimate', 'type': ['null', 'int'], 'default': None, 'doc': 'Estimated duration of the ride (in seconds).'},
        {'name': 'fare_estimate', 'type': ['null', 'double'], 'default': None, 'doc': 'Estimated fare for the ride.'},
        {
            'name': 'feedback',
            'type': [
                'null',
                {
                    'type': 'record',
                    'name': 'Feedback',
                    'fields': [
                        {'name': 'rating', 'type': 'int'},
                        {'name': 'comments', 'type': 'string'}
                    ]
                }
            ],
            'default': None,
            'doc': 'Feedback provided by the passenger.'
        }
    ]
}

# Parse the schema
parsed_passenger_schema = parse_schema(passenger_request_schema)

# Define the driver schema
driver_schema = {
    'doc': 'A driver availability feed schema.',
    'name': 'Driver',
    'namespace': 'stream.ride.information',
    'type': 'record',
    'fields': [
        {'name': 'event_id', 'type': 'string', 'doc': 'Unique identifier for this event'},
        {'name': 'driver_id', 'type': 'string'},
        {'name': 'timestamp', 'type': 'long', 'doc': 'Timestamp of status update'},
        {
            'name': 'location',
            'type': {
                'name': 'Location',
                'type': 'record',
                'fields': [
                    {'name': 'latitude', 'type': 'float'},
                    {'name': 'longitude', 'type': 'float'}
                ]
            }
        },
        {
            'name': 'status',
            'type': {
                'type': 'enum',
                'name': 'Status',
                'symbols': ['available', 'en route', 'engaged', 'offline']
            },
            'doc': 'Current driver status.'
        },
        {'name': 'ride_id', 'type': ['null', 'string'], 'default': None},
        {
            'name': 'vehicle_type',
            'type': {
                'name': 'VehicleTypeEnum',
                'type': 'enum',
                'symbols': ['sedan', 'suv', 'van', 'truck', 'hatchback']
            }
        },
        {'name': 'driver_session_id', 'type': 'string'},
        {
            'name': 'traffic_condition',
            'type': ['null', {
                'name': 'TrafficConditionEnum',
                'type': 'enum',
                'symbols': ['light', 'moderate', 'heavy', 'gridlock', 'unknown']
            }],
            'default': None
        }
    ]
}

# Parse the schema
parsed_driver_schema = parse_schema(driver_schema)