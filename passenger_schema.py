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