from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask import current_app as app
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
from datetime import datetime
from functools import wraps

from config import SERVICE_API_TOKEN, MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, TEST_MODE, TEST_EMAIL, ADMIN_PASSWORD
from functions_db_helpers import insert_user, remove_user, get_users_by_email_list, get_email_lists, insert_subscription, remove_subscription, get_user_subscriptions, get_user_emails, insert_feedback, get_email_feedback, get_email_list_by_id
from functions_dispatch import generate_content_and_dispatch, send_email


app = Flask(__name__)

### CONFIG ----------------------
# Configuration for the admin authentication
app.config['ADMIN_PASSWORD'] = ADMIN_PASSWORD

# external service api token
app.config['SERVICE_API_TOKEN'] = SERVICE_API_TOKEN

# Flask-mail config
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

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
        auth_header = request.headers.get('token')
        
        if not auth_header:
            return jsonify({"message": "Missing token"}), 401

        # The token is usually sent as "Bearer <token>"
        try:
            token = auth_header
        except IndexError:
            return jsonify({"message": "Invalid token format"}), 401

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
                    batch_id TEXT,
                    date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(email_list_id) REFERENCES email_lists(id)
                 )''')

    # Feedback table
    c.execute('''DROP TABLE IF EXISTS email_feedback''')  # Drop the existing email history table if it exists
    c.execute('''CREATE TABLE IF NOT EXISTS email_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER,
                    user_id INTEGER,
                    rating INTEGER,
                    comment TEXT,
                    FOREIGN KEY(email_id) REFERENCES emails(id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                 )''')
    
    conn.commit()
    conn.close()


def init_db_test_data():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()

    # Insert example users
    example_users = [
        ('42523','Robert H', TEST_EMAIL),
        ('75437','Grace S', TEST_EMAIL),
        ('54642','Alice Johnson', TEST_EMAIL)
    ]
    c.executemany('''INSERT INTO users (external_key, name, email) 
                     VALUES (?, ?, ?)''', example_users)

    # Insert example email lists
    example_email_lists = [
        (1,'myrecord_weekly'),
        (2,'decide2')
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
        (1, 1, "test_batch1"),  #user_id, email_list_id, batch_id
        (1, 1, "test_batch1"),  
        (2, 1, "test_batch2"),  
        (2, 1, "test_batch2"),  
        (3, 2, "test_batch2"),  
    ]
    c.executemany('''INSERT INTO emails (user_id, email_list_id, batch_id) VALUES (?, ?,?)''', example_emails)

    # Insert example feedback
    example_feedback = [
        (1, 1, 1, "Too big"),  
        (2, 1, 2, "Too small"),  
        (3, 2, 3, "Too wide"),  
        (4, 2, 4, "Too narrow"),  
        (5, 3, 5, "Just right"),  
    ]
    c.executemany('''INSERT INTO email_feedback (email_id, user_id, rating, comment) VALUES (?, ?, ?, ?)''', example_feedback)

    conn.commit()
    conn.close()



### APP ROUTES ---------------------------
#API - USER MANAGEMENT
# API endpoint to add users
@app.route('/api/add_user', methods=['GET','POST'])
@requires_auth_api
def add_user():
    data = request.json
    external_key = data.get('external_key')
    name = data.get('name')
    email = data.get('email')

    if not name or not email or not external_key:
        return jsonify({'error': 'External key, name and email are required'}), 400

    insert_user(external_key, name, email)
    return jsonify({'message': 'User added successfully'}), 201

# API endpoint to retrieve a user's subscriptions and email history
@app.route('/api/user/<external_key>', methods=['GET'])
@requires_auth_api
def user_subscriptions(external_key):
    # Check if the user exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE external_key = ?''', (external_key,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Get user's subscriptions
    c.execute('''SELECT email_list_id, date_subscribed FROM user_subscriptions WHERE user_id = ?''', (user[0],))
    subscriptions = c.fetchall()

    # Get user's email history
    emails = get_user_emails(user[0])

    conn.close()

    # Prepare subscription and email history data
    subscription_list = [{'email_list_id': sub[0],'date_subscribed': sub[1]} for sub in subscriptions]
    emails_list = [{'email_list_id': hist[0], 'date_sent': hist[1], 'batch_id':hist[2]} for hist in emails]

    return jsonify({
        'id': user[0],
        'external_key': user[1],
        'name': user[2],
        'email': user[3],
        'subscriptions': subscription_list,
        'emails': emails_list
    }), 200



# API - SUBSCRIPTION MANAGEMENT
# API endpoint to add a subscription for a user
@app.route('/api/add_subscription/<external_key>/<int:email_list_id>', methods=['GET','POST'])
@requires_auth_api
def add_subscription(external_key, email_list_id):
    # Check if the user exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE external_key = ?''', (external_key,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Add subscription
    insert_subscription(user[0], email_list_id)
    conn.close()
    return jsonify({'message': f'Subscription added'}), 201

# API endpoint to remove a subscription for a user
@app.route('/api/delete_subscription/<external_key>/<int:email_list_id>', methods=['GET','DELETE'])
@requires_auth_api
def delete_subscription(external_key, email_list_id):
    # Check if the user exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE external_key = ?''', (external_key,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Remove subscription
    remove_subscription(user[0], email_list_id)
    conn.close()
    return jsonify({'message': f'Subscription removed'}), 200

### USER INTERFACE ---------------------------
# Route to reset the database
@app.route('/reset_database')
@requires_auth
def reset_database():
    init_db()  # Call the function to initialize the database and add example users
    return 'Database reset successfully'

# Route to display homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to unsubscribe a user from an email list
@app.route('/unsubscribe/<int:user_id>/<int:email_list_id>', methods=['GET', 'POST'])
def unsubscribe(user_id, email_list_id):
    if request.method == 'GET':
        # You may want to check if the user is subscribed to the email list before rendering the page
        return render_template('unsubscribe.html', user_id=user_id, email_list_id=email_list_id)
    elif request.method == 'POST':
        # Process the unsubscribe action
        remove_subscription(user_id, email_list_id)
        return render_template('unsubscribed.html') # Redirect to homepage or any other page after unsubscribing


# Route for the admin page
@app.route('/admin')
@requires_auth
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
    c.execute('''SELECT users.id, users.name, email_lists.email_list_name, emails.date_sent, emails.batch_id
                 FROM users
                 LEFT JOIN emails ON users.id = emails.user_id
                 LEFT JOIN email_lists ON emails.email_list_id = email_lists.id''')
    email_history = c.fetchall()

    conn.close()

    jobs = scheduler.get_jobs()

    return render_template('admin.html', email_lists=email_lists, users_subscriptions=users_subscriptions, email_history=email_history, jobs=jobs)

@app.route('/logout')
def logout():
    """Simulate a logout by sending a 401 response."""
    return Response(
        'You have been logged out.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


# Export data
# Function to fetch data from the database and format it as CSV
def export_data():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()

    # Query emails table joined with email_feedback table
    c.execute('''SELECT e.email_list_id, e.user_id, e.id AS email_id, e.date_sent, e.batch_id
                        f.id AS feedback_id, f.rating, f.comment
                 FROM emails e
                 LEFT JOIN email_feedback f ON e.id = f.email_id AND e.user_id = f.user_id''')
    data = c.fetchall()

    conn.close()

    # Format data as CSV
    csv_data = [
        ['email_list_id', 'user_id', 'email_id', 'date_sent', 'batch_id', 'feedback_id', 'rating', 'comment'],
        *data
    ]

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


# Route to trigger sending of test email
@app.route('/send_test_email', methods=['GET', 'POST'])
@requires_auth
def send_test_email():
    if request.method == 'POST':
        send_email(TEST_EMAIL,"Test email","This is a test email sent from Flask.")  # Call the function to send the email
        return redirect(url_for('index'))  # Redirect to homepage or any other page
    return render_template('send_test_email.html')


# Route to trigger manual dispatch of an email list
@app.route('/manual_dispatch/<int:email_list_id>', methods=['GET', 'POST'])
@requires_auth
def manual_dispatch(email_list_id):
    email_list = get_email_list_by_id(email_list_id)
    if request.method == 'POST':
        stdout, stderr = generate_content_and_dispatch(email_list_id)  # Call the function to send generate and dispatch
        return render_template('script_log.html', stdout=stdout, stderr=stderr)  # Redirect to homepage or any other page
    return render_template('manual_dispatch.html',email_list=email_list)



@app.route('/create-job', methods=['GET'])
@requires_auth
def create_job_form():

    # Fetch email lists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM email_lists''')
    email_lists = c.fetchall()

    """Render the form to create a new scheduled job."""
    return render_template('create_job.html',email_lists=email_lists)

@app.route('/create-job', methods=['POST'])
@requires_auth
def create_job():
    """Handle creating a new scheduled job."""
    job_name = request.form['job_name']
    email_list_id = request.form['email_list']
    start_date_str = request.form['start_datetime']
    days = int(request.form['days'])


    # Parse the start date string into a datetime object
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        # Handle the error, e.g., return an error message to the user
        return "Invalid date format. Please use YYYY-MM-DDTHH:MM format.", 400

    #days= request.form['days']
    args = [email_list_id]

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
scheduler = BackgroundScheduler()
scheduler.start()

# Initialize Flask-Mail
mail = Mail(app)

if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    if TEST_MODE:
        init_db_test_data()
    app.run(debug=True)
    
