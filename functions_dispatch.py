from time import sleep
from yaml import safe_load
import subprocess
import sqlite3
from datetime import datetime
from flask_mail import Message
import csv

from config import RSCRIPT_PATH, INDICIA_USER, INDICIA_SECRET
from functions_db_helpers import get_users_by_email_list, add_email_sent

### SENDING EMAILS FUNCTIONALITY -----------------------
# Dispatch feedback
def dispatch_feedback(recipient_internal_id,subject,html):
    # Check if the user exists
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE id = ?''', (recipient_internal_id,))
    user = c.fetchone()
    if not user:
        raise Exception("No user found with that ID")
    
    from config import DISPATCH_METHOD
    if DISPATCH_METHOD == 'email':
        send_email(user[3],subject,html)
    elif DISPATCH_METHOD == 'indicia_notifications':
        send_indicia_notification(user[1],subject,html)
    else:
        raise Exception("DISPATCH_METHOD not recognised")

# Function to send email
def send_email(recipient,subject,html):
    from app import app, mail
    with app.app_context():
        msg = Message(subject=subject, recipients=[recipient])
        msg.html = html
        mail.send(msg)
        print("Email sent successfully at", datetime.now())

#function to send feedback via indicia notifications
def send_indicia_notification(recipient_indicia_id,subject,html):
    INDICIA_USER
    INDICIA_SECRET
    print("This is where code will go about using indicia api to POST notifications")

# Function to export users from the database to the csv used in recorder-feedback
def export_users_csv(file, email_list_id):
    # Query users from your database
    users = get_users_by_email_list(email_list_id)

    # Define CSV file headers
    fields = ['user_id', 'name', 'email', 'Date Created']

    # Create a CSV file in memory
    with open(file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write headers to the CSV file
        writer.writerow(fields)

        # Write user data to the CSV file
        for user in users:
            writer.writerow(user)

    return users #return the filename


# function to trigger the email content generation
def generate_content_and_dispatch(email_list_id):
    # STEP1: Export users from flask database
    # get the name of the email list
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''SELECT email_list_name FROM email_lists WHERE id = ?''', (email_list_id,)) # Query to get the name of the email list by its ID
    result = c.fetchone()
    conn.close()
    email_list_name = result[0]
    print(email_list_name)

    # Get the user file location from the config file
    f = open('R/'+email_list_name+'/config.yml', 'r')
    yaml_content = f.read()
    data = safe_load(yaml_content)
    
    # Get the users and export as csv
    users = export_users_csv('R/'+email_list_name+'/'+data['default']['participant_data_file'],email_list_id)

    # STEP2: Run email generation code
    # Trigger email generation
    r_script_file = 'R/'+email_list_name+'/generate_feedback_items.R'

    # Call the R script using subprocess.Popen
    batch_id = datetime.today().strftime('%Y_%m_%d_%H_%M_%S')
    process = subprocess.Popen(RSCRIPT_PATH+" "+r_script_file+" "+batch_id, 
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE
                               )

    process.wait()

    # Capture the output and error
    stdout_r, stderr_r = process.communicate()

    # end the pipeline and show the R code if the pipeline failed
    if not "ended pipeline" in stdout_r.decode('utf-8'):
        return stdout_r.decode('utf-8'), stderr_r.decode('utf-8')

    #STEP3 get the filepath of the rendered data
    # Load the user meta data
    # Define the path to your CSV file
    csv_file_path = 'R/'+email_list_name+'/renders/'+batch_id+'/meta_table_'+batch_id+'.csv' # Update this with the actual path

    # Initialize an empty list to store tuples of user ID and file path
    file_paths = []

    # Open the CSV file and read its contents
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row if it exists
        for row in reader:
            user_id, file_path = row
            user_id = int(user_id)
            file_paths.append((user_id,'R/'+email_list_name+'/'+file_path))

    
    user_data_dict = {user[0]: user[1:] for user in users} # Create a dictionary to map user IDs to their data
    joined_data = [] # Initialize an empty list to store the joined data

    # Iterate through the file_paths list
    for user_id, file_path in file_paths:
        if user_id in user_data_dict:
            # Combine user data with file path
            joined_data.append((user_id,) + user_data_dict[user_id] + (file_path,))

    # Print the joined data
    print(joined_data)


    #STEP4 send emails
    # Loop through users, send email and log email send
    for user in joined_data:
        sleep(2)
        print("Sending email to:")
        print(user[3])
        print("Email content:")
        print(user[4])
        #get html content
        with open(user[4], "r") as f:
            html_content = f.read()
        dispatch_feedback(user[0],email_list_name,html_content)
        add_email_sent(user[0], email_list_id)

    return stdout_r.decode('utf-8'), stderr_r.decode('utf-8')