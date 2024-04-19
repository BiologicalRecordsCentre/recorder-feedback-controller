from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import current_app as app
import sqlite3
from datetime import datetime

from config import API_KEY, REQUIRE_KEY

app = Flask(__name__)

# Configuration for the API key
app.config['API_KEY'] = API_KEY
app.config['REQUIRE_KEY'] = REQUIRE_KEY

# Function to initialize the database with the updated schema
def init_db():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS users''')  # Drop the existing table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    email TEXT,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')

    # Insert example users
    example_users = [
        ('John Doe', 'john@example.com'),
        ('Jane Smith', 'jane@example.com'),
        ('Alice Johnson', 'alice@example.com')
    ]
    c.executemany('''INSERT INTO users (name, email) 
                     VALUES (?, ?)''', example_users)

    conn.commit()
    conn.close()



# Function to insert user data into the database
def insert_user(name, email):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users (name, email) 
                 VALUES (?, ?)''', 
              (name, email))
    conn.commit()
    conn.close()

# Function to remove a user from the database
def remove_user(user_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''DELETE FROM users WHERE id = ?''', (user_id,))
    conn.commit()
    conn.close()

# Function to get all users from the database
def get_all_users():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT id, name, email, date_created FROM users''')
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


# API endpoint to add users
@app.route('/api/add_user', methods=['GET','POST'])
def add_user():
    api_key = request.headers.get('API-Key')
    if api_key != app.config['API_KEY'] and app.config['REQUIRE_KEY']:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.json
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400

    insert_user(name, email)
    return jsonify({'message': 'User added successfully'}), 201

# API endpoint to remove a user
@app.route('/api/remove_user/<int:user_id>', methods=['GET','POST','DELETE'])
def delete_user(user_id):
    api_key = request.headers.get('API-Key')
    if api_key != app.config['API_KEY'] and app.config['REQUIRE_KEY']:
        return jsonify({'error': 'Invalid API key'}), 401

    # Check if the user exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE id = ?''', (user_id,))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    remove_user(user_id)
    return jsonify({'message': 'User removed successfully'}), 200

# API endpoint to retrieve user information
@app.route('/api/users', methods=['GET'])
def get_users():
    api_key = request.headers.get('API-Key')
    if api_key != app.config['API_KEY'] and app.config['REQUIRE_KEY']:
        return jsonify({'error': 'Invalid API key'}), 401

    users = get_all_users()
    user_list = []
    for user in users:
        user_dict = {
            'id': user[0],
            'name': user[1],
            'email': user[2],
            'date_created': user[3]
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
