# Ride_Hailing_Stream

# Data Feed Generation

This repository is designed to generate and manage data feeds for a simulation of driver-passenger interactions in a ride-sharing environment. The main functionality involves creating realistic driver and passenger event data, assigning drivers to passenger requests, and determining the outcomes (completed rides or cancellations).

## Repository Contents

- **`data_feed_generation.py`**: Main script to generate and process driver and passenger data.
- **`driver_avail_schema.py`**: Schema definition for driver data in Avro format.
- **`passenger_schema.py`**: Schema definition for passenger request data in Avro format.
- **Generated Files**:
  - `drivers.json`: JSON file containing the final state of all drivers.
  - `drivers.avro`: Avro file containing driver data.
  - `passenger_requests.json`: JSON file containing the final state of all passenger requests.
  - `passenger_requests.avro`: Avro file containing passenger request data.

### Generated Files Overview

1. **Drivers JSON and Avro Files**:
   - Represent the final state of all drivers.
   - At the end of the process, all drivers are marked as `available`.

2. **Passenger Requests JSON and Avro Files**:
   - Represent the final state of all passenger requests.
   - Requests are either marked as `completed` or `canceled`, with associated details (e.g., feedback for completed requests or cancellation reasons).

### Key Notes

- The JSON files (`drivers.json` and `passenger_requests.json`) contain the final processed version of all events.
- Drivers are evenly distributed among passenger requests through a matching algorithm.
- All iterations and intermediate logs of driver-passenger interactions will be implemented in the next step of development.

## Next Steps

The next phase will involve adding functionality to log the detailed iterations of driver-passenger interactions, providing a step-by-step view of how each event was processed and resolved.

