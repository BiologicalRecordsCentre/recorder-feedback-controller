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

    # Insert examplelists
    example_lists = [
        (1,'myrecord_weekly', "Every week you get a nice summary of what you've recorded, how nice!"),
        (2,'decide2',"Like DECIDE, but better!")
    ]
    c.executemany('''INSERT INTO lists (id, name,description) VALUES (?, ?, ?)''', example_lists)


    # Insert example subscriptions
    example_subscriptions = [
        (1, 1),  #user_id, list_id
        (1, 2),  
        (2, 1),  
        (3, 2),  
    ]
    c.executemany('''INSERT INTO subscriptions (user_id, list_id) VALUES (?, ?)''', example_subscriptions)               

    # Insert example email history
    example_items = [
        (1, 1, "test_batch1"),  #user_id, list_id, batch_id
        (1, 1, "test_batch1"),  
        (2, 1, "test_batch2"),  
        (2, 1, "test_batch2"),  
        (3, 2, "test_batch2"),  
    ]
    c.executemany('''INSERT INTO items (user_id, list_id, batch_id) VALUES (?, ?,?)''', example_items)

    conn.commit()
    conn.close()