from config import TEST_EMAIL
import sqlite3

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
        (1,'myrecord_weekly', "Every week you get a nice summary of what you've recorded, how nice!"),
        (2,'decide2',"Like DECIDE, but better!")
    ]
    c.executemany('''INSERT INTO email_lists (id, email_list_name,description) VALUES (?, ?, ?)''', example_email_lists)


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