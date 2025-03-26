from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask import current_app as app
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
import json

from config import SERVICE_API_TOKEN, AUTHENTICATE_API, SQLALCHEMY_DATABASE_URI, MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USE_SSL, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, TEST_EMAIL, TEST_EXTERNAL_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

app = Flask(__name__)

### CONFIG ----------------------
# Configuration for the admin authentication
app.config['ADMIN_USERNAME'] = ADMIN_USERNAME
app.config['ADMIN_PASSWORD'] = ADMIN_PASSWORD

# external service api token
app.config['AUTHENTICATE_API'] = AUTHENTICATE_API
app.config['SERVICE_API_TOKEN'] = SERVICE_API_TOKEN

# Flask-mail config
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

### AUTHENTICATION DECORATORS
# Function to check authentication
def check_auth(username, password):
    """Check if a username/password combination is valid."""
    return username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']

# Function to request authentication
def authenticate():
    """Send a 401 response that enables basic auth"""
    return Response(
        'Could not verify your login.\n'
        'You must provide valid credentials to access this page.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

# Decorator to require authentication (for admin pages)
def is_running_on_posit():
    """Check if the app is running on Posit Connect by looking for a specific header."""
    return "Rstudio-Connect-Credentials" in request.headers

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if is_running_on_posit():
            from config import APPLICATION_ROOT
            app.config["APPLICATION_ROOT"] = APPLICATION_ROOT

            # Posit Connect authentication
            credentials = request.headers.get("Rstudio-Connect-Credentials")
            if credentials:
                credentials_dict = json.loads(credentials)
                username = credentials_dict.get("user")

                if username == app.config["ADMIN_USERNAME"]:
                    return f(*args, **kwargs)
            
            return authenticate()
        else:
            # Basic Auth (for local development)
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
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    external_key = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(250))

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)
    date_subscribed = db.Column(db.DateTime, default=datetime.utcnow)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_key = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)
    batch_id = db.Column(db.String(120))
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)

class FeedbackOnItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_content_key = db.Column(db.String(120), db.ForeignKey('item.content_key'), nullable=False)  # Foreign key to content_key
    item = db.relationship('Item', backref=db.backref('feedback', lazy=True))
    comment = db.Column(db.String(250))
    date = db.Column(db.DateTime, default=datetime.utcnow)

def init_db():
    db.create_all()

def init_db_test_data():
    # Insert example users
    example_users = [
        User(external_key=TEST_EXTERNAL_KEY, name='Simon Rolph', email=TEST_EMAIL)
    ]
    db.session.bulk_save_objects(example_users)

    # Insert example lists
    example_lists = [
        List(id=1, name='myrecord_weekly', description="Every week you get a nice summary of what you've recorded, how nice!"),
        List(id=2, name='decide2', description="Like DECIDE, but better!")
    ]
    db.session.bulk_save_objects(example_lists)

    # Insert example subscriptions
    example_subscriptions = [
        Subscription(user_id=1, list_id=1),
        Subscription(user_id=1, list_id=2)
    ]
    db.session.bulk_save_objects(example_subscriptions)

    # Insert example email history
    example_items = [
        Item(user_id=1, content_key = "43242", list_id=1, batch_id="test_batch1"),
        Item(user_id=1, content_key = "23523", list_id=1, batch_id="test_batch1"),
        Item(user_id=1, content_key = "53233", list_id=1, batch_id="test_batch2")
    ]
    db.session.bulk_save_objects(example_items)

    db.session.commit()



def insert_user(external_key, name, email):
    user = User(external_key=external_key, name=name, email=email)
    db.session.add(user)
    db.session.commit()

def get_user_by_external_key(external_key):
    return User.query.filter_by(external_key=external_key).first()

def update_user_by_id(user_id, external_key, name, email):
    user = User.query.get(user_id)
    if user:
        user.external_key = external_key
        user.name = name
        user.email = email
        db.session.commit()

def remove_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()

def get_users_by_list(list_id):
    return User.query.join(Subscription).filter(Subscription.list_id == list_id).all()

def get_lists():
    return List.query.all()

def get_list_name(list_id):
    list = List.query.get(list_id)
    return list.name if list else None

def get_list_by_id(list_id):
    return List.query.get(list_id)

def insert_subscription(user_id, list_id):
    subscription = Subscription(user_id=user_id, list_id=list_id)
    user = User.query.get(user_id)
    db.session.add(subscription)
    db.session.commit()
    send_email(user.email, "Unsubscribed", f"You have been subscribed {get_list_name(list_id)}")

def remove_subscription(user_id, list_id):
    subscription = Subscription.query.filter_by(user_id=user_id, list_id=list_id).first()
    user = User.query.get(user_id)
    if subscription:
        db.session.delete(subscription)
        db.session.commit()
        send_email(user.email, "Unsubscribed", f"You have been unsubscribed from {get_list_name(list_id)}")

def get_subscriptions(user_id):
    return Subscription.query.filter_by(user_id=user_id).all()

def check_subscription(user_id, list_id):
    return Subscription.query.filter_by(user_id=user_id, list_id=list_id).first()

def add_item_sent(user_id, list_id, batch_id):
    item = Item(user_id=user_id, list_id=list_id, batch_id=batch_id)
    db.session.add(item)
    db.session.commit()

def get_user_items(user_id):
    return Item.query.filter_by(user_id=user_id).all()



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
        'id': user.id,
        'external_key': user.external_key,
        'name': user.name,
        'email': user.email
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
    
    if user.external_key == external_key:
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
    user_id = user.id

    #ge the IDs for all the lists the user is subscribed to
    subscriptions = get_subscriptions(user_id)
    subscription_ids = []
    for subscription in subscriptions:
        subscription_ids.append(
            subscription.id
        )

    # Create a response list showing all lists and subscription status
    feedback_lists = get_lists()
    subscription_status = []
    for feedback_lists in feedback_lists:
        is_subscribed = feedback_lists.id in subscription_ids
        subscription_status.append({
            'id': feedback_lists.id,
            'name': feedback_lists.name,
            'description': feedback_lists.description,
            'subscribed': is_subscribed
        })

    return jsonify({
        'id': user_id,
        'external_key': user.external_key,
        'name': user.name,
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
    
    user_id = user.id
    
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

    user_id = user.id
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
            'id': feedback_list.id,
            'name': feedback_list.name,
            'description': feedback_list.description,
        })
    
    # Return the feedback lists in JSON format
    return jsonify({'lists': feedback_list_data}), 200


# API endpoint to get all users subscribed to a specific list
@app.route('/api/lists/<list_id>', methods=['GET'])
@requires_auth_api
def api_get_list_subscribers(list_id):

    list_details = get_list_by_id(list_id)
    
    # Retrieve all user ids subscribed to the given list
    subscribers = db.session.query(Subscription.user_id).filter_by(list_id=list_id).all()
    
    if not subscribers:
        return jsonify({'error': 'No subscribers found for this list'}), 404
    
    # Get details for each subscribed user
    user_data = []
    for subscriber in subscribers:
        user_id = subscriber[0]
        user = User.query.filter_by(id=user_id).first()
        if user:
            user_data.append({
                'id': user.id,
                'external_key': user.external_key,
                'name': user.name,
                'email': user.email
            })
    
    
    # Return the list of subscribers in JSON format
    return jsonify({'id': list_details.id,
                    'name' : list_details.name,
                    'description' : list_details.description,
                    'subscribers': user_data}), 200


@app.route('/api/items', methods=['POST'])
@requires_auth_api
def create_item():
    data = request.get_json()
    content_key = str(data.get('content_key'))
    user_external_key = data.get('user_external_key')
    list_id = data.get('list_id')
    batch_id = data.get('batch_id')

    if not content_key or not user_external_key or not list_id:
        return jsonify({'error': 'Missing required fields'}), 400

    user_id = get_user_by_external_key(user_external_key).id

    new_item = Item(
        content_key=content_key,
        user_id=user_id,
        list_id=list_id,
        batch_id=batch_id
    )
    db.session.add(new_item)
    db.session.commit()

    return jsonify({'message': 'Item created successfully', 'item': {
        'id': new_item.id,
        'content_key': new_item.content_key,
        'user_id': new_item.user_id,
        'list_id': new_item.list_id,
        'batch_id': new_item.batch_id,
        'date_sent': new_item.date_sent
    }}), 201


## USER FACING
# Webpage so a user can unsubscribe themselves
@app.route('/unsubscribe/<item_content_key>', methods=['GET', 'POST'])
def unsubscribe(item_content_key):
    item = Item.query.filter_by(content_key=item_content_key).first()
    list_id = item.list_id
    user_id = item.user_id
    if request.method == 'GET':
        list = get_list_by_id(list_id)
        user = User.query.get(user_id)
        # You may want to check if the user is subscribed to the email list before rendering the page
        return render_template('unsubscribe.html', user=user, list=list)
    elif request.method == 'POST':
        # Process the unsubscribe action
        remove_subscription(user_id, list_id)
        return render_template('unsubscribed.html') # Redirect to homepage or any other page after unsubscribing

@app.route('/submit_feedback/<item_content_key>', methods=['GET', 'POST'])
def submit_feedback(item_content_key):
    if request.method == 'POST':
        comment = request.form['comment']

        feedback = FeedbackOnItem(item_content_key=item_content_key, comment=comment)
        db.session.add(feedback)
        db.session.commit()
        return render_template('submitted_feedback.html')
    return render_template('submit_feedback.html', item_content_key=item_content_key)


### ADMIN ---------------------------
# Route for the admin page
@app.route('/admin')
@requires_auth
def admin():
    # Fetch lists
    lists = List.query.all()

    # Fetch users and their subscriptions
    users = User.query.all()
    subscriptions = Subscription.query.all()
    feedback = FeedbackOnItem.query.all()

    # Fetch items history
    items = Item.query.all()

    return render_template('admin.html', lists=lists, users=users, subscriptions=subscriptions, items=items,feedback = feedback)

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
    db.drop_all()
    db.create_all()  # Initialize the database when the app starts
    init_db_test_data() # Insert test data into the database
    return redirect(url_for('admin'))

# Route to trigger sending of test email
@app.route('/send_test_email', methods=['GET', 'POST'])
@requires_auth
def send_test_email():
    if request.method == 'POST':
        send_email(TEST_EMAIL,"Test email","This is a test email sent from Flask.")  # Call the function to send the email
        return redirect(url_for('index'))  # Redirect to homepage or any other page
    return render_template('send_test_email.html')


# page to create a new list
@app.route('/create_list', methods=['GET', 'POST'])
@requires_auth
def create_list():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        list = List(name=name, description=description)
        db.session.add(list)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('create_list.html')

# Initialize Flask-Mail
mail = Mail(app)

# Function to send email
def send_email(recipient,subject,html):
    from app import app, mail
    with app.app_context():
        msg = Message(subject=subject, recipients=[recipient])
        msg.html = html
        mail.send(msg)
        print("Email sent successfully at", datetime.now())


if __name__ == '__main__':
    app.run(debug=True)


