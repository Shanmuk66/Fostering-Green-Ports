import time
from datetime import datetime, timedelta
from db import create_connection
# Initialize the berthing and waiting lobbies
berthing_lobby = {}
waiting_lobby = {}

# Define the berthing capacity and waiting capacity
berthing_capacity = 10
waiting_capacity = 15

# Define the ship size mapping, berthing time, and emission index mapping
ship_size_mapping = {"Small": 4, "Medium": 3, "Large": 2, "Ultra Large": 1}
berthing_time = {"Small": 8, "Medium": 16, "Large": 24, "Ultra Large": 32}
emission_index_mapping = {"High": 1, "Moderate": 2, "Low": 3}

# Define the priority mapping
priority_mapping = {
    "Emergencies (vessel damage)": 1,
    "Humanitarian aid & relief operation": 2,
    "Environmental concerns": 3,
    "Pre arranged priority": 4,
    "Deadlock Waiting": 5,
    "No priority": 6
}

# List of available berths
available_berths = {berth: False for berth in range(1, berthing_capacity + 1)}

# Function to check the status of the ships and manage ship departures
def check_status_and_departures():
#     print("Checking status and managing departures:")
    current_time = time.time()
    for ship_id, ship_info in list(berthing_lobby.items()):
        arrival_time = datetime.datetime.fromtimestamp(ship_info['arrival_time']).strftime('%Y-%m-%d %H:%M:%S')
        time_remaining = ship_info['berthing_time'] - (current_time - ship_info['arrival_time'])
        if time_remaining <= 0:
            ship_leaves(ship_id)
        else:
            time_remaining_str = str(timedelta(seconds=int(time_remaining)))
            print(f"Ship ID: {ship_id}, Berth Number: {ship_info['berth_number']}, Status: Berthing, Arrival Time: {arrival_time}, Time Remaining for Berthing: {time_remaining_str}")

# Function to check if there's any vacancy in the berthing lobby
def available_berths_check():
    for berth, status in available_berths.items():
        if not status:
            return berth

import datetime

# Function to handle the berthing process for a ship
def ship_arrives(ship_id, ship_size, ship_priority, ship_emission_index):
    print(f"Ship {ship_id} has arrived.")
    arrival_time = time.time()
    if len(berthing_lobby) < berthing_capacity:
        # Assign a berth to the ship and add it to the berthing lobby
        berth_number = available_berths_check()
        available_berths[berth_number] = True
        berthing_time_seconds = berthing_time[ship_size]  # Calculate berthing time in seconds
        berthing_lobby[ship_id] = {"size": ship_size, "priority": ship_priority, "emission_index": ship_emission_index, "arrival_time": arrival_time, "berth_number": berth_number, "berthing_time": berthing_time_seconds}  # Add berthing_time
        # Connect to the database and insert values
        conn = create_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE ship_infoo
                SET Berth = ?,
                    from_time = ?,
                    to_time = ?
                WHERE id = ?
            ''', (int(berth_number), arrival_time, arrival_time + berthing_time_seconds, ship_id))
            conn.commit()
            conn.close()
            print(f"Berth details updated for Ship {ship_id}.")
            from_time = datetime.datetime.fromtimestamp(arrival_time).strftime('%Y-%m-%d %H:%M:%S')
            to_time = datetime.datetime.fromtimestamp(arrival_time + berthing_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            print(f"Ship {ship_id} has been assigned to Berth {berth_number} from {from_time} to {to_time}.")
        else:
            print('Error: Unable to connect to the database')

    else:
        # Add the ship to the waiting lobby
        waiting_lobby[ship_id] = {"size": ship_size, "priority": ship_priority, "emission_index": ship_emission_index, "arrival_time": arrival_time}
        print(f"Ship {ship_id} has been added to the waiting lobby.")
    #call main function
    

# Function to handle the ship leaving the berthing lobby
def ship_leaves(ship_id):
    print(f"Ship {ship_id} has left.")
    available_berths[berthing_lobby[ship_id]['berth_number']] = False
    del berthing_lobby[ship_id]
    vacancy_arises()      
             
# Function to handle vacancy arising in the berthing lobby
def vacancy_arises():
    if len(waiting_lobby) > 0:
        # Calculate the score for each ship in the waiting lobby
        ship_scores = {}
        for ship_id, ship_info in waiting_lobby.items():
            score = priority_mapping[ship_info['priority']] * 10 + emission_index_mapping[ship_info['emission_index']]
            ship_scores[ship_id] = score
        # Sort the ships by score and arrival time
        sorted_ships = sorted(ship_scores.items(), key=lambda x: (x[1], waiting_lobby[x[0]]['arrival_time']))
        # Select the ship with the highest score and move it to the berthing lobby
        selected_ship_id = sorted_ships[0][0]
        selected_ship_info = waiting_lobby[selected_ship_id]  
        selected_ship_size = selected_ship_info['size']
        selected_ship_priority = selected_ship_info['priority']
        selected_ship_emission_index = selected_ship_info['emission_index']
        del waiting_lobby[selected_ship_id]
        ship_arrives(selected_ship_id, selected_ship_size, selected_ship_priority, selected_ship_emission_index)

# Simulate ship arrivals
# ship_arrives("Ship1", "Large", "Pre arranged priority", "Moderate")
# ship_arrives("Ship2", "Small", "Emergencies (vessel damage)", "High")
# ship_arrives("Ship3", "Ultra Large", "Humanitarian aid & relief operation", "Low")
# ship_arrives("Ship4", "Medium", "Environmental concerns", "Moderate")
# ship_arrives("Ship5", "Medium", "Pre arranged priority", "High")
# ship_arrives("Ship6", "Small", "Deadlock Waiting", "Low")
# ship_arrives("Ship7", "Large", "Deadlock Waiting", "High")

if __name__ == "__main__":
    # Check status and manage ship departures
    while True:
        if len(berthing_lobby) > 0 or len(waiting_lobby) > 0:
            check_status_and_departures()
        time.sleep(1)  # Check every second
