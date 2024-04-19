from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import current_app as app
import sqlite3
from datetime import datetime

from config import API_KEY

app = Flask(__name__)

# Configuration for the API key
app.config['API_KEY'] = API_KEY

# Function to initialize the database with the updated schema
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS users''')  # Drop the existing table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    email TEXT,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    latitude REAL,
                    longitude REAL,
                    radius_km REAL,
                    indicia_id TEXT
                 )''')

    # Insert example users
    example_users = [
        ('John Doe', 'john@example.com', 40.7128, -74.0060, 10, 'abc123'),
        ('Jane Smith', 'jane@example.com', 34.0522, -118.2437, 15, 'def456'),
        ('Alice Johnson', 'alice@example.com', 51.5074, -0.1278, 20, 'ghi789')
    ]
    c.executemany('''INSERT INTO users (name, email, latitude, longitude, radius_km, indicia_id) 
                     VALUES (?, ?, ?, ?, ?, ?)''', example_users)

    conn.commit()
    conn.close()



# Function to insert user data into the database
def insert_user(name, email, latitude, longitude, radius_km, indicia_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users (name, email, latitude, longitude, radius_km, indicia_id) 
                 VALUES (?, ?, ?, ?, ?, ?)''', 
              (name, email, latitude, longitude, radius_km, indicia_id))
    conn.commit()
    conn.close()

# Function to get all users from the database
def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT id, name, email, date_created, latitude, longitude, radius_km, indicia_id FROM users''')
    users = c.fetchall()
    conn.close()
    return users


# Route to reset the database
@app.route('/reset_database')
def reset_database():
    init_db()  # Call the function to initialize the database and add example users
    return 'Database reset successfully'

# Route to display homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to display all users in a table
@app.route('/ui/users')
def users():
    users = get_all_users()
    return render_template('users.html', users=users)

# Route to display the form for user input
@app.route('/ui/add_user')
def signup():
    return render_template('signup.html')

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    radius_km = request.form['radius_km']
    indicia_id = request.form['indicia_id']
    insert_user(name, email, latitude, longitude, radius_km, indicia_id)
    return redirect(url_for('signup'))




# API endpoint to add users
@app.route('/api/add_user', methods=['GET','POST'])
def add_user():
    api_key = request.headers.get('API-Key')
    if api_key != app.config['API_KEY']:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.json
    name = data.get('name')
    email = data.get('email')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    radius_km = data.get('radius_km')
    indicia_id  = data.get('indicia_id')

    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400

    insert_user(name, email, latitude, longitude, radius_km, indicia_id)
    return jsonify({'message': 'User added successfully'}), 201

# API endpoint to retrieve user information
@app.route('/api/users', methods=['GET'])
def get_users():
    api_key = request.headers.get('API-Key')
    #if api_key != app.config['API_KEY']:
    #    return jsonify({'error': 'Invalid API key'}), 401

    users = get_all_users()
    user_list = []
    for user in users:
        user_dict = {
            'id': user[0],
            'name': user[1],
            'email': user[2],
            'date_created': user[3],
            'latitude': user[4],
            'longitude': user[5],
            'radius_km': user[6],
            'indicia_id': user[7]
        }
        user_list.append(user_dict)
    response = {
        'num_results': len(user_list),
        'users': user_list
    }
    return jsonify(response), 200

if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    app.run(debug=True)
