import sqlite3
### DATABASE HELPERS ------------------------------
# MANAGE USERS
# Function to insert user data into the database
def insert_user(external_key, name, email):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users (external_key, name, email) 
                 VALUES (?, ?, ?)''', 
              (external_key, name, email))
    conn.commit()
    conn.close()

# Function to remove a user from the database
def remove_user(user_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''DELETE FROM users WHERE id = ?''', (user_id,))
    conn.commit()
    conn.close()

# Function to get users based on their email list
def get_users_by_email_list(email_list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    # Query to get users subscribed to a particular email list
    c.execute('''SELECT users.id, users.external_key, users.name, users.email
                 FROM users
                 INNER JOIN user_subscriptions ON users.id = user_subscriptions.user_id
                 WHERE user_subscriptions.email_list_id = ?''', (email_list_id,))
    users = c.fetchall()
    conn.close()
    return users

def get_email_lists():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    # Query to get all email lists
    c.execute('''SELECT * FROM email_lists''')
    email_lists = c.fetchall()
    conn.close()
    return email_lists


def get_list_name(email_list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    # Query to get users subscribed to a particular email list
    c.execute('''SELECT * FROM email_lists WHERE id = ?''', (email_list_id,))
    list = c.fetchone()
    conn.close()
    return list[1]

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
def add_email_sent(user_id, email_list_id, batch_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO emails (user_id, email_list_id, batch_id) 
                 VALUES (?, ?, ?)''', 
              (user_id, email_list_id, batch_id))
    conn.commit()
    conn.close()

# Function to get email history for a user
def get_user_emails(user_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT email_list_id, date_sent, batch_id FROM emails WHERE user_id = ?''', (user_id,))
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


# EMAIL LISTs
def get_email_list_by_id(email_list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM email_lists WHERE id = ?''', (email_list_id,)) # Query to get the name of the email list by its ID
    email_list = c.fetchone()
    conn.close()
    return email_list