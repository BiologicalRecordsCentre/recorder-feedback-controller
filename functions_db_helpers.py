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

#get user by external key
def get_user_by_external_key(external_key):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT id, external_key, name, email 
                 FROM users WHERE external_key = ?''', (external_key,))
    user = c.fetchone()
    conn.close()

    if user:
        return user
    return None

def update_user_by_id(user_id, external_key, name, email):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''UPDATE users 
                 SET external_key = ?, name = ?, email = ? 
                 WHERE id = ?''', 
              (external_key, name, email, user_id))
    conn.commit()
    conn.close()

# Function to remove a user from the database
def remove_user(user_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''DELETE FROM users WHERE id = ?''', (user_id,))
    conn.commit()
    conn.close()

# Function to get users based on their list
def get_users_by_list(list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    # Query to get users subscribed to a particular list
    c.execute('''SELECT users.id, users.external_key, users.name, users.email
                 FROM users
                 INNER JOIN subscriptions ON users.id = subscriptions.user_id
                 WHERE subscriptions.list_id = ?''', (list_id,))
    users = c.fetchall()
    conn.close()
    return users

def get_lists():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    # Query to get all lists
    c.execute('''SELECT * FROM lists''')
    lists = c.fetchall()
    conn.close()
    return lists


def get_list_name(list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    # Query to get users subscribed to a particular list
    c.execute('''SELECT * FROM lists WHERE id = ?''', (list_id,))
    list = c.fetchone()
    conn.close()
    return list[1]

def get_list_by_id(list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM lists WHERE id = ?''', (list_id,)) # Query to get the name of the  list by its ID
    list = c.fetchone()
    conn.close()
    return list

#MANAGE SUBSCRIPTIONS
# Function to add subscription for a user
def insert_subscription(user_id, list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO subscriptions (user_id, list_id) 
                 VALUES (?, ?)''', 
              (user_id, list_id))
    conn.commit()
    conn.close()

# Function to remove subscription for a user
def remove_subscription(user_id, list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''DELETE FROM subscriptions WHERE user_id = ? AND list_id = ?''', 
              (user_id, list_id))
    conn.commit()
    conn.close()

# Function to get all subscriptions for a user
def get_subscriptions(user_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM subscriptions WHERE user_id = ?''', (user_id,))
    subscriptions = c.fetchall()
    conn.close()
    return subscriptions

def check_subscription(user_id, list_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM subscriptions WHERE user_id = ? AND list_id = ?''', (user_id,list_id,))
    subscription = c.fetchone()

    if subscription:
        return subscription
    return None

# MANAGE EMAILS
# Function to add item dispatch history
def add_item_sent(user_id, list_id, batch_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO items (user_id, list_id, batch_id) 
                 VALUES (?, ?, ?)''', 
              (user_id, list_id, batch_id))
    conn.commit()
    conn.close()

# Function to get item history for a user
def get_user_items(user_id):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT list_id, date_sent, batch_id FROM items WHERE user_id = ?''', (user_id,))
    history = c.fetchall()
    conn.close()
    return history


