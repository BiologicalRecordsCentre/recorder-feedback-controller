from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask import current_app as app
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
from datetime import datetime
from functools import wraps

from config import SERVICE_API_TOKEN, AUTHENTICATE_API, MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, TEST_MODE, TEST_EMAIL, ADMIN_PASSWORD, USE_SCHEDULER
from functions_db_helpers import insert_user, get_user_by_external_key, update_user_by_id, remove_user, get_users_by_list, get_lists, insert_subscription, remove_subscription, get_subscriptions, get_user_items, get_list_by_id, get_list_name, check_subscription
from functions_dispatch import generate_content_and_dispatch, send_email, dispatch_feedback
from functions_test_data import init_db_test_data

app = Flask(__name__)

### CONFIG ----------------------
# Configuration for the admin authentication
app.config['ADMIN_PASSWORD'] = ADMIN_PASSWORD

# external service api token
app.config['AUTHENTICATE_API'] = AUTHENTICATE_API
app.config['SERVICE_API_TOKEN'] = SERVICE_API_TOKEN

# Flask-mail config
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

app.config['USE_SCHEDULER'] = USE_SCHEDULER

### AUTHENTICATION DECORATORS
# Function to check authentication
def check_auth(username, password):
    """Check if a username/password combination is valid."""
    return username == 'admin' and password == app.config['ADMIN_PASSWORD']

# Function to request authentication
def authenticate():
    """Send a 401 response that enables basic auth"""
    return Response(
        'Could not verify your login.\n'
        'You must provide valid credentials to access this page.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

# Decorator to require authentication (for admin pages)
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_auth_api(token):
    """Check if the token is valid."""
    return token == app.config['SERVICE_API_TOKEN']

# Decorator to require authentication (for API)
def requires_auth_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If in test mode, proceed with the original function
        if not app.config['AUTHENTICATE_API']:
            return f(*args, **kwargs)

        # Get the Authorization header
        auth_header = request.headers.get('Authorization')

        # Check if Authorization header is provided
        if not auth_header:
            return jsonify({"message": "Missing token"}), 401

        # Extract the token from the Authorization header
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != 'Bearer':
            return jsonify({"message": "Invalid token format"}), 401

        token = parts[1]

        # Validate the token
        if not check_auth_api(token):
            return jsonify({"message": "Unauthorized"}), 401

        # If the token is valid, proceed with the original function
        return f(*args, **kwargs)

    return decorated_function

# Function to initialize the database
def init_db():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()

    # USERS
    c.execute('''DROP TABLE IF EXISTS users''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    external_key TEXT,
                    name TEXT, 
                    email TEXT,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')

    # lists
    c.execute('''DROP TABLE IF EXISTS lists''')  # Drop the existing table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT,
                    description TEXT
                 )''')

    # subscriptions to lists
    c.execute('''DROP TABLE IF EXISTS subscriptions''')  # Drop the existing subscription table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    list_id INTEGER,
                    date_subscribed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(list_id) REFERENCES lists(id)
                 )''')

    #item history
    c.execute('''DROP TABLE IF EXISTS items''')  # Drop the existing item history table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    list_id INTEGER,
                    batch_id TEXT,
                    date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(list_id) REFERENCES lists(id)
                 )''')
    
    conn.commit()
    conn.close()



### APP ROUTES ---------------------------
# Route to display homepage
@app.route('/')
def index():
    return render_template('index.html')


#API --------------------------------------------
# API endpoint to add users
@app.route('/api/users', methods=['POST'])
@requires_auth_api
def api_create_user():
    data = request.json
    external_key = data.get('external_key')
    name = data.get('name')
    email = data.get('email')

    user = get_user_by_external_key(external_key)
    if user:
        return jsonify({'error': 'User already exists with this external_key'}), 400

    if not external_key or not name or not email:
        return jsonify({'error': 'External key, name, and email are required'}), 400

    insert_user(external_key, name, email)
    return jsonify({'message': 'User added successfully'}), 201

# API endpoint to get user by external_key
@app.route('/api/users/<external_key>', methods=['GET'])
@requires_auth_api
def api_get_user(external_key):
    user = get_user_by_external_key(external_key)
    print(user)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Assuming user is returned as a tuple with (id, external_key, name, email)
    user_data = {
        'id': user[0],
        'external_key': user[1],
        'name': user[2],
        'email': user[3]
    }
    
    return jsonify(user_data), 200

# API endpoint to update users
@app.route('/api/users/<external_key>', methods=['PUT'])
@requires_auth_api
def api_update_user(external_key):
    data = request.json
    external_key = data.get('external_key')
    name = data.get('name')
    email = data.get('email')

    if not external_key or not name or not email:
        return jsonify({'error': 'External key, name, and email are required'}), 400
    
    user = get_user_by_external_key(external_key)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user[1] == external_key:
        return jsonify({'error': 'User already exists with this external_key'}), 400

    update_user_by_id(user[0], external_key, name, email)
    return jsonify({'message': 'User updated successfully'}), 200

# Retrieve a user's subscriptions
@app.route('/api/users/<external_key>/subscriptions', methods=['GET'])
@requires_auth_api
def api_get_subscriptions(external_key):
    user = get_user_by_external_key(external_key)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    #get the user id
    user_id = user[0]

    #ge the IDs for all the lists the user is subscribed to
    subscriptions = get_subscriptions(user_id)
    subscription_ids = []
    for subscription in subscriptions:
        subscription_ids.append(
            subscription[2]
        )

    # Create a response list showing all lists and subscription status
    feedback_lists = get_lists()
    subscription_status = []
    for feedback_lists in feedback_lists:
        is_subscribed = feedback_lists[0] in subscription_ids
        subscription_status.append({
            'id': feedback_lists[0],
            'name': feedback_lists[1],
            'description': feedback_lists[2],
            'subscribed': is_subscribed
        })

    return jsonify({
        'id': user_id,
        'external_key': user[1],
        'name': user[2],
        'lists': subscription_status,
    }), 200

# Add a subscription for a user
@app.route('/api/users/<external_key>/subscriptions', methods=['POST'])
@requires_auth_api
def api_add_user_subscription(external_key):
    data = request.json
    list_id = data.get('list_id')

    if not list_id:
        return jsonify({'error': 'Email list ID is required'}), 400

    user = get_user_by_external_key(external_key)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_id = user[0]
    
    subscription = check_subscription(user_id,list_id)

    if subscription:
        return jsonify({'error': 'Subscription already exists'}), 400

    insert_subscription(user_id, list_id)
    
    return jsonify({'message': 'Subscription added successfully'}), 201

# Remove a subscription for a user
@app.route('/api/users/<external_key>/subscriptions/<list_id>', methods=['DELETE'])
@requires_auth_api
def api_remove_user_subscription(external_key, list_id):
    user = get_user_by_external_key(external_key)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_id = user[0]
    remove_subscription(user_id, list_id)
    
    return jsonify({'message': 'Subscription removed successfully'}), 200

# API endpoint to get all feedback lists
@app.route('/api/lists', methods=['GET'])
@requires_auth_api
def api_get_feedback_lists():
    # Retrieve all feedback lists from the databaser
    feedback_lists = get_lists() 
    
    # Prepare the response data
    feedback_list_data = []
    for feedback_list in feedback_lists:
        feedback_list_data.append({
            'id': feedback_list[0],
            'name': feedback_list[1],
            'description': feedback_list[2],
        })
    
    # Return the feedback lists in JSON format
    return jsonify({'lists': feedback_list_data}), 200

# Webpage so a user can unsubscribe themselves
#@app.route('/unsubscribe/<int:user_id>/<int:email_list_id>', methods=['GET', 'POST'])
#def unsubscribe(user_id, email_list_id):
#    if request.method == 'GET':
#        # You may want to check if the user is subscribed to the email list before rendering the page
#        return render_template('unsubscribe.html', user_id=user_id, email_list_id=email_list_id)
#    elif request.method == 'POST':
#        # Process the unsubscribe action
#        remove_subscription(user_id, email_list_id)
#        return render_template('unsubscribed.html') # Redirect to homepage or any other page after unsubscribing


### ADMIN ---------------------------
# Route for the admin page
@app.route('/admin')
@requires_auth
def admin():
    # Fetch lists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM lists''')
    lists = c.fetchall()

    c.execute('''SELECT * FROM users''')
    users = c.fetchall()

    # Fetch users and their subscriptions
    c.execute('''SELECT * FROM subscriptions''')
    subscriptions = c.fetchall()

    # Fetch items history
    c.execute('''SELECT * FROM items''')
    items = c.fetchall()

    conn.close()
    
    if app.config['USE_SCHEDULER']:
        jobs = scheduler.get_jobs()
    else: 
        jobs = []

    return render_template('admin.html', lists=lists, users=users, subscriptions=subscriptions, items=items, jobs=jobs)

@app.route('/logout')
def logout():
    """Simulate a logout by sending a 401 response."""
    return Response(
        'You have been logged out.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


# Export data
# Function to fetch data from the database and format it as CSV
def export_data():
    csv_data =[]
    return csv_data

# Route to export the data as a csv
@app.route('/export_data')
@requires_auth
def export_data_page():
    # Fetch data
    data = export_data()

    # Set up CSV response
    csv_data = ''.join([','.join(map(str, row)) + '\n' for row in data])
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=data.csv'

    return response


# Route to export the data as a csv
@app.route('/reset_data')
@requires_auth
def reset_data():
    init_db()
    init_db_test_data()
    return redirect(url_for('admin'))

# Route to trigger sending of test email
@app.route('/send_test_email', methods=['GET', 'POST'])
@requires_auth
def send_test_email():
    if request.method == 'POST':
        send_email(TEST_EMAIL,"Test email","This is a test email sent from Flask.")  # Call the function to send the email
        return redirect(url_for('index'))  # Redirect to homepage or any other page
    return render_template('send_test_email.html')


# Route to trigger manual dispatch of an email list
@app.route('/manual_dispatch/<int:list_id>', methods=['GET', 'POST'])
@requires_auth
def manual_dispatch(list_id):
    list = get_list_by_id(list_id)
    if request.method == 'POST':
        stdout, stderr = generate_content_and_dispatch(list_id)  # Call the function to send generate and dispatch
        return render_template('script_log.html', stdout=stdout, stderr=stderr)  # Redirect to homepage or any other page
    return render_template('manual_dispatch.html',list=list)



@app.route('/create-job', methods=['GET'])
@requires_auth
def create_job_form():

    # Fetch email lists
    lists = get_lists()

    """Render the form to create a new scheduled job."""
    return render_template('create_job.html',lists=lists)

@app.route('/create-job', methods=['POST'])
@requires_auth
def create_job():
    """Handle creating a new scheduled job."""
    job_name = request.form['job_name']
    list_id = request.form['list']
    start_date_str = request.form['start_datetime']
    days = int(request.form['days'])


    # Parse the start date string into a datetime object
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        # Handle the error, e.g., return an error message to the user
        return "Invalid date format. Please use YYYY-MM-DDTHH:MM format.", 400

    #days= request.form['days']
    args = [list_id]

    scheduler.add_job(generate_content_and_dispatch, 'interval',args=args,start_date = start_date,name = job_name,days = days)

    return redirect(url_for('admin'))

# Route to delete a scheduled job
@app.route('/delete-job/<job_id>', methods=['POST'])
@requires_auth
def delete_job(job_id):
    """Handle deleting a scheduled job."""
    job = scheduler.get_job(job_id)
    if job:
        scheduler.remove_job(job_id)
        return redirect(url_for('admin'))
    else:
        return jsonify({'error': 'Job not found'}), 404



### APP ----------------
# Initialize scheduler
if app.config['USE_SCHEDULER']:
    scheduler = BackgroundScheduler()
    scheduler.start()


# Initialize Flask-Mail
mail = Mail(app)

if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    init_db_test_data()
    app.run(debug=True)


