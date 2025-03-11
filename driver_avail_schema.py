from fastavro import writer, reader, parse_schema
import io


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