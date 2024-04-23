from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import current_app as app
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
from datetime import datetime

from config import API_KEY, REQUIRE_KEY, MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER

app = Flask(__name__)

# Configuration for the API key
app.config['API_KEY'] = API_KEY
app.config['REQUIRE_KEY'] = REQUIRE_KEY

# Flask-mail config
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

# Initialize Flask-Mail
mail = Mail(app)

# Function to initialize the database
def init_db():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()

    # USERS
    c.execute('''DROP TABLE IF EXISTS users''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    email TEXT,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')

    # email_lists
    c.execute('''DROP TABLE IF EXISTS email_lists''')  # Drop the existing table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS email_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    email_list_name TEXT
                 )''')

    # subscriptions to email lists
    c.execute('''DROP TABLE IF EXISTS user_subscriptions''')  # Drop the existing subscription table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS user_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    email_list_id INTEGER,
                    date_subscribed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(email_list_id) REFERENCES email_lists(id)
                 )''')

    #email history
    c.execute('''DROP TABLE IF EXISTS emails''')  # Drop the existing email history table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    email_list_id INTEGER,
                    date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(email_list_id) REFERENCES email_lists(id)
                 )''')

    # Feedback table
    c.execute('''CREATE TABLE IF NOT EXISTS email_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER,
                    user_id INTEGER,
                    rating INTEGER,
                    comment TEXT,
                    FOREIGN KEY(email_id) REFERENCES emails(id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                 )''')

    # Insert example users
    example_users = [
        ('John Doe', 'john@example.com'),
        ('Jane Smith', 'jane@example.com'),
        ('Alice Johnson', 'alice@example.com')
    ]
    c.executemany('''INSERT INTO users (name, email) 
                     VALUES (?, ?)''', example_users)

    # Insert example email lists
    example_email_lists = [
        (1,'MyRecord weekly'),
        (2,'DECIDE2')
    ]
    c.executemany('''INSERT INTO email_lists (id, email_list_name) VALUES (?, ?)''', example_email_lists)


    # Insert example subscriptions
    example_subscriptions = [
        (1, 1),  #user_id, email_list_id
        (1, 2),  
        (2, 1),  
        (3, 2),  
    ]
    c.executemany('''INSERT INTO user_subscriptions (user_id, email_list_id) VALUES (?, ?)''', example_subscriptions)               

    # Insert example email history
    example_emails = [
        (1, 1),  #user_id, email_list_id
        (1, 1),  
        (2, 1),  
        (2, 1),  
        (3, 2),  
    ]
    c.executemany('''INSERT INTO emails (user_id, email_list_id) VALUES (?, ?)''', example_emails)

    conn.commit()
    conn.close()


# MANAGE USERS
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

#MANAGE SUBSCRIPTIONS
# Function to add subscription for a user
def insert_subscription(user_id, email_list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO user_subscriptions (user_id, email_list_id) 
                 VALUES (?, ?)''', 
              (user_id, email_list_id))
    conn.commit()
    conn.close()

# Function to remove subscription for a user
def remove_subscription(user_id, email_list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''DELETE FROM user_subscriptions WHERE user_id = ? AND email_list_id = ?''', 
              (user_id, email_list_id))
    conn.commit()
    conn.close()

# Function to get all subscriptions for a user
def get_user_subscriptions(user_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT id, email_list_id, date_subscribed FROM user_subscriptions WHERE user_id = ?''', (user_id,))
    subscriptions = c.fetchall()
    conn.close()
    return subscriptions

# MANAGE EMAILS
# Function to add email sending history
def add_email_sent(user_id, email_list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO emails (user_id, email_list_id) 
                 VALUES (?, ?)''', 
              (user_id, email_list_id))
    conn.commit()
    conn.close()

# Function to get email history for a user
def get_user_emails(user_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT email_list_id, date_sent FROM emails WHERE user_id = ?''', (user_id,))
    history = c.fetchall()
    conn.close()
    return history


# FEEDBACK
# Function to insert user feedback into the database
def insert_feedback(email_id, user_id, rating, comment):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO email_feedback (email_id, user_id, rating, comment) 
                 VALUES (?, ?, ?, ?)''', (email_id, user_id, rating, comment))
    conn.commit()
    conn.close()

# Function to get feedback for a specific email
def get_email_feedback(email_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM email_feedback WHERE email_id = ?''', (email_id,))
    feedback = c.fetchall()
    conn.close()
    return feedback

# APP ROUTES
# Route to reset the database
@app.route('/reset_database')
def reset_database():
    init_db()  # Call the function to initialize the database and add example users
    return 'Database reset successfully'

# Route to display homepage
@app.route('/')
def index():
    return render_template('index.html')


#API - USER MANAGEMENT
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

# API endpoint to retrieve list of user
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

# API endpoint to retrieve a user's subscriptions and email history
@app.route('/api/user/<int:user_id>', methods=['GET'])
def user_subscriptions(user_id):
    api_key = request.headers.get('API-Key')
    if api_key != app.config['API_KEY'] and app.config['REQUIRE_KEY']:
        return jsonify({'error': 'Invalid API key'}), 401

    # Check if the user exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE id = ?''', (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Get user's subscriptions
    c.execute('''SELECT email_list_id, date_subscribed FROM user_subscriptions WHERE user_id = ?''', (user_id,))
    subscriptions = c.fetchall()

    # Get user's email history
    emails = get_user_emails(user_id)

    conn.close()

    # Prepare subscription and email history data
    subscription_list = [{'email_list_id': sub[0],'date_subscribed': sub[1]} for sub in subscriptions]
    emails_list = [{'email_list_id': hist[0], 'date_sent': hist[1]} for hist in emails]

    return jsonify({
        'id': user_id,
        'name': user[1],
        'email': user[2],
        'subscriptions': subscription_list,
        'emails': emails_list
    }), 200



# API - SUBSCRIPTION MANAGEMENT
# API endpoint to add a subscription for a user
@app.route('/api/add_subscription/<int:user_id>/<int:email_list_id>', methods=['POST'])
def add_subscription(user_id, email_list_id):
    api_key = request.headers.get('API-Key')
    if api_key != app.config['API_KEY'] and app.config['REQUIRE_KEY']:
        return jsonify({'error': 'Invalid API key'}), 401

    # Check if the user exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE id = ?''', (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Add subscription
    insert_subscription(user_id, email_list_id)
    conn.close()
    return jsonify({'message': f'Subscribed {user[1]} to {email_list_id}'}), 201

# API endpoint to remove a subscription for a user
@app.route('/api/delete_subscription/<int:user_id>/<int:email_list_id>', methods=['DELETE'])
def delete_subscription(user_id, email_list_id):
    api_key = request.headers.get('API-Key')
    if api_key != app.config['API_KEY'] and app.config['REQUIRE_KEY']:
        return jsonify({'error': 'Invalid API key'}), 401

    # Check if the user exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE id = ?''', (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Remove subscription
    remove_subscription(user_id, email_list_id)
    conn.close()
    return jsonify({'message': f'Unsubscribed {user[1]} from {email_list_id}'}), 200

#PROVIDING FEEDBACK
# Update API endpoint to add user feedback
@app.route('/api/add_feedback/<int:email_id>', methods=['POST'])
def add_feedback(email_id):

    data = request.json
    user_id = data.get('user_id')
    rating = data.get('rating')
    comment = data.get('comment')

    if not user_id or not rating or not comment:
        return jsonify({'error': 'User ID, rating, and comment are required'}), 400

    # Check if the email history ID exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM emails WHERE id = ?''', (email_id,))
    emails = c.fetchone()
    conn.close()

    if not emails:
        return jsonify({'error': 'Email history not found'}), 404

    insert_feedback(email_id, user_id, rating, comment)
    return jsonify({'message': 'Feedback added successfully'}), 201

# Route to unsubscribe a user from an email list
@app.route('/unsubscribe/<int:user_id>/<int:email_list_id>', methods=['GET', 'POST'])
def unsubscribe(user_id, email_list_id):
    if request.method == 'GET':
        # You may want to check if the user is subscribed to the email list before rendering the page
        return render_template('unsubscribe.html', user_id=user_id, email_list_id=email_list_id)
    elif request.method == 'POST':
        # Process the unsubscribe action
        remove_subscription(user_id, email_list_id)
        return redirect(url_for('index'))  # Redirect to homepage or any other page after unsubscribing

# Route for the admin page
@app.route('/admin')
def admin():
    # Fetch email lists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM email_lists''')
    email_lists = c.fetchall()

    # Fetch users and their subscriptions
    c.execute('''SELECT users.id, users.name, users.email, email_lists.email_list_name
                 FROM users
                 LEFT JOIN user_subscriptions ON users.id = user_subscriptions.user_id
                 LEFT JOIN email_lists ON user_subscriptions.email_list_id = email_lists.id''')
    users_subscriptions = c.fetchall()

    # Fetch email history
    c.execute('''SELECT users.id, users.name, email_lists.email_list_name, emails.date_sent
                 FROM users
                 LEFT JOIN emails ON users.id = emails.user_id
                 LEFT JOIN email_lists ON emails.email_list_id = email_lists.id''')
    email_history = c.fetchall()

    conn.close()

    return render_template('admin.html', email_lists=email_lists, users_subscriptions=users_subscriptions, email_history=email_history)







# Function to send email
def send_email():
    with app.app_context():
        msg = Message(subject="Test Email", recipients=["simrol@ceh.ac.uk"])
        msg.body = "This is a test email sent from Flask."
        mail.send(msg)
        print("Email sent successfully at", datetime.now())

# Route to trigger sending of test email
@app.route('/send_test_email', methods=['GET', 'POST'])
def send_test_email():
    if request.method == 'POST':
        send_email()  # Call the function to send the email
        return redirect(url_for('index'))  # Redirect to homepage or any other page
    return render_template('send_test_email.html')



# # Initialize scheduler
# scheduler = BackgroundScheduler()
# scheduler.start()

# # Schedule the email sending job
# scheduler.add_job(send_email, 'interval', minutes=5)  # Send email every 5 minutes




if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    app.run(debug=True)
