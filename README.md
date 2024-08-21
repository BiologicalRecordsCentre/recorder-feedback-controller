# Recorder Feedback Controller App

## Overview

A flask app for user management and dispatch of personalised feedback for biological recording.

App requirements:

 * Define and host a database for holding information on:
    * Subscribers - email address, identifiers for recording platforms
    * Email lists - the different email lists
    * Subscriptions - who has subscribed to what email lists
    * Email history - logging who has received what emails
    * Feedback on emails - capturing user feedback on the emails they have recevied
 * Provide API endpoints as the main way of interacting with the database
    * User creation
    * Subscribing / unsubscribing
    * Logging email dispatching
 * Provide limited webpages
    * One click email unsubscribe (to meet GDPR requirements)
    * Admin log-in
 * Host email generation R code: https://github.com/BiologicalRecordsCentre/recorder-feedback
 * Send emails on a schedule
 * Export user provided feedback

## Development start up

### Install Python, pip and virtualenv

This has been developed with Python 3.12. pip is required for package management.

Python installation: https://www.python.org/downloads/ (or from the Software Centre if at UKCEH). Ensure it has been added to PATH environment variable https://realpython.com/add-python-to-path/
pip installation: https://pip.pypa.io/en/stable/installation/
Install virtualvenv: `python -m pip install virtualenv`

### Get the code

Clone repo:
`git clone https://github.com/simonrolph/recorder-feedback-controller.git`
   
Navigate inside folder:
`cd recorder-feedback-controller`

### Install packages

#### Option 1: Using virtualenv (preferred)

Create virtualenv
`python -m virvualenv venv`

Activate the virtualenv (not possible on UKCEH managed machines because of IT policies)
`venv\Scripts\activate` (windows)
`source venv/bin/activate` (unix)

#### Option 2: Not using virtualenv

Install packages using pip to the user library
`python -m pip install flask flask_mail apscheduler pyyaml`

### Initial set up

Create the config.py by copying from config_example.py and filling in details

Create a folder named `data`

### Run the app

```
python app.py
```

Then navigate to `http://127.0.0.1:5000/`

The database structure described in your Flask application code consists of several interconnected tables designed to manage users, email lists, subscriptions, email history, and feedback. Below is a detailed explanation of each table and its relationships:

## App functionality

### Tables and Schema

1. **Users Table**
   - **Purpose:** To store user information.
   - **Columns:**
     - `id`: Integer, Primary Key, Auto-incremented.
     - `name`: Text, stores the user's name.
     - `email`: Text, stores the user's email.
     - `date_created`: Timestamp, stores the date and time the user was created, defaulting to the current timestamp.

2. **Email Lists Table**
   - **Purpose:** To store different email lists.
   - **Columns:**
     - `id`: Integer, Primary Key, Auto-incremented.
     - `email_list_name`: Text, stores the name of the email list.

3. **User Subscriptions Table**
   - **Purpose:** To link users to email lists, representing their subscriptions.
   - **Columns:**
     - `id`: Integer, Primary Key, Auto-incremented.
     - `user_id`: Integer, Foreign Key referencing `users(id)`, stores the ID of the user.
     - `email_list_id`: Integer, Foreign Key referencing `email_lists(id)`, stores the ID of the email list.
     - `date_subscribed`: Timestamp, stores the date and time the user subscribed, defaulting to the current timestamp.

4. **Emails Table**
   - **Purpose:** To track the emails sent to users.
   - **Columns:**
     - `id`: Integer, Primary Key, Auto-incremented.
     - `user_id`: Integer, Foreign Key referencing `users(id)`, stores the ID of the user.
     - `email_list_id`: Integer, Foreign Key referencing `email_lists(id)`, stores the ID of the email list.
     - `date_sent`: Timestamp, stores the date and time the email was sent, defaulting to the current timestamp.

5. **Email Feedback Table**
   - **Purpose:** To store feedback provided by users for specific emails.
   - **Columns:**
     - `id`: Integer, Primary Key, Auto-incremented.
     - `email_id`: Integer, Foreign Key referencing `emails(id)`, stores the ID of the email.
     - `user_id`: Integer, Foreign Key referencing `users(id)`, stores the ID of the user.
     - `rating`: Integer, stores the user's rating of the email.
     - `comment`: Text, stores the user's comment on the email.

### Relationships Between Tables

- **Users** and **Email Lists** are connected through the **User Subscriptions** table, forming a many-to-many relationship.
- **Users** and **Emails** are connected through the **Emails** table, where each record represents an email sent to a user.
- **Emails** and **Email Feedback** are connected through the **Email Feedback** table, which captures user feedback on specific emails.

### Functions

The code includes several helper functions to manage the data:

- **User Management:**
  - `insert_user(name, email)`: Adds a new user.
  - `remove_user(user_id)`: Deletes a user.
  - `get_all_users()`: Retrieves all users.
  - `get_users_by_email_list(email_list_id)`: Retrieves users subscribed to a specific email list.

- **Subscription Management:**
  - `insert_subscription(user_id, email_list_id)`: Adds a subscription for a user.
  - `remove_subscription(user_id, email_list_id)`: Removes a subscription for a user.
  - `get_user_subscriptions(user_id)`: Retrieves all subscriptions for a user.

- **Email Management:**
  - `add_email_sent(user_id, email_list_id)`: Logs an email sent to a user.
  - `get_user_emails(user_id)`: Retrieves the email history for a user.

- **Feedback Management:**
  - `insert_feedback(email_id, user_id, rating, comment)`: Adds feedback for an email.
  - `get_email_feedback(email_id)`: Retrieves feedback for a specific email.

### API Endpoints

The application provides several API endpoints to manage users, subscriptions, and feedback, and to interact with the database:

- `/api/add_user`: Adds a new user.
- `/api/remove_user/<int:user_id>`: Deletes a user.
- `/api/users`: Retrieves all users.
- `/api/user/<int:user_id>`: Retrieves a user's subscriptions and email history.
- `/api/add_subscription/<int:user_id>/<int:email_list_id>`: Adds a subscription for a user.
- `/api/delete_subscription/<int:user_id>/<int:email_list_id>`: Removes a subscription for a user.
- `/api/add_feedback/<int:email_id>`: Adds feedback for an email.
