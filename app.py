import sqlite3
from datetime import datetime
import numpy as np
from flask import Flask, render_template, request, redirect, jsonify
import joblib
import pandas as pd
from flask import jsonify
from milpp import ship_arrives
from db import create_connection
import logging

app = Flask(__name__)

# Load the trained model
rf_classifier = joblib.load('trained_model.pkl')

# Load the dataset and preprocess it to get X
data = pd.read_csv("emissions_dataset2.csv")
data = data.drop(columns=['Ship Type'])
X = data.drop(columns=['emissions'])

# Function to create the table if it doesn't exist
def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ship_infoo (
                id INTEGER PRIMARY KEY,
                ship_type TEXT NOT NULL,
                ship_size INTEGER NOT NULL,
                vessel_age INTEGER NOT NULL,
                fuel_type INTEGER NOT NULL,
                fuel_consumption INTEGER NOT NULL,
                engine_type INTEGER NOT NULL,
                emission_control_technologies INTEGER NOT NULL,
                load_factor INTEGER NOT NULL,
                Emissions INTEGER,
                Berth INTEGER DEFAULT 0,
                from_time TIMESTAMP DEFAULT NULL,
                to_time TIMESTAMP DEFAULT NULL
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(e)


@app.route('/submit', methods=['POST'])
def submit():
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ship_infoo (ship_type, ship_size, vessel_age, fuel_type, fuel_consumption, engine_type,
                                   emission_control_technologies, load_factor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (request.form['ship-type'], request.form['ship-size'], request.form['vessel-age'],
              request.form['fuel-type'], request.form['fuel-consumption'], request.form['engine-type'],
              request.form['emission-control'], request.form['load-factor']))
        priority=request.form['priority']
        # Retrieve the last inserted row's id
        last_id = cursor.lastrowid
        print(last_id)
        
        # Commit the transaction and close the connection
        conn.commit()
        # conn.close()

        # Get input values
        input_values = [ request.form['ship-size'], request.form['fuel-type'], int(request.form['vessel-age']),
                         request.form['fuel-consumption'], request.form['engine-type'],
                         request.form['emission-control'], int(request.form['load-factor'])]
        
        # Convert input values to DataFrame
        input_data = pd.DataFrame([input_values], columns=X.columns)
        
        # Predict emissions using the trained model
        predicted_emissions = rf_classifier.predict(input_data)[0]
        predicted_emissions = int(predicted_emissions)

        # Update Emissions column for the last inserted row
        cursor.execute('''
            UPDATE ship_infoo
            SET Emissions = ?
            WHERE id = ?
        ''', (predicted_emissions, last_id))
        
        # Commit the transaction
        conn.commit()
        
        # Close the connection
        conn.close()
        # Mapping of predicted_emissions values to emission levels
        emission_levels = {
            0: "Low",
            1: "Moderate",
            2: "High"
        }
        sizeOfShip_levels={
            "0": "Large",
            "2": "Small",
            "1": "Medium"
        }
        sizeOfShip=sizeOfShip_levels.get(request.form['ship-size'])
        emission_level = emission_levels.get(predicted_emissions, "Unknown")
        # Call ship_arrives function
        ship_arrives(str(last_id), sizeOfShip, priority, emission_level)  # Pass appropriate parameters
        
        return render_template('check.html', status_message="Check your ship status.", ship_id=last_id,emission_level=emission_level)
        
    else:
        return 'Error: Unable to connect to the database'


@app.route('/check')
def check():
    ship_id = request.args.get('ship_id')
    emission_level=request.args.get('emission_level')
    # Connect to the database
    conn = create_connection()
    cursor = conn.cursor()
    
    # Retrieve the ship information from the database based on the ship_id
    cursor.execute('''
        SELECT Berth, from_time, to_time
        FROM ship_infoo
        WHERE id = ?
    ''', (ship_id,))
    ship_info = cursor.fetchone()  # Fetch one row
    
    # Close the database connection
    conn.close()
    
    # Check if ship_info is not None (i.e., ship_id exists in the database)
    if ship_info:
        berth, from_time, to_time = ship_info
        
        # app.logger.info(f"Ship {ship_id} has been assigned to Berth {berth} from {from_time_str} to {to_time_str}.")
        
        if berth == 0:
            # If the ship is in the waiting lobby, display a message
            return render_template('check.html', status_message="Your ship is in the waiting lobby.", ship_id=ship_id)
        else:
            # If the ship has been allocated a berth, form the message
            from_time_str = datetime.fromtimestamp(from_time).strftime('%Y-%m-%d %H:%M:%S')
            to_time_str = datetime.fromtimestamp(to_time).strftime('%Y-%m-%d %H:%M:%S')
            return render_template('result.html', berth=berth, from_time=from_time_str, to_time=to_time_str, emission_level=emission_level)

            
    else:
        # If ship_id does not exist in the database, display an error message
        return render_template('check.html', status_message="Ship ID not found in the database.",ship_id= ship_id)


@app.route('/')
def home():
    return render_template('home2.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/intimate')
def intimate():
    return render_template('intimate.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

@app.route('/result')
def result():
    return render_template('result.html')

if __name__ == '__main__':
    app.run(debug=True)
