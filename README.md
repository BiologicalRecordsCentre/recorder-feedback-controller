![](https://github.com/BiologicalRecordsCentre/recorder-feedback/blob/main/Recorder%20feedback%20logo_small.png?raw=true)  

# Recorder Feedback Controller App

Part of the Recorder Feedback system: https://github.com/BiologicalRecordsCentre/recorder-feedback

## Overview

Biological recorders contribute valuable biodiversity data; and extensive infrastructure exists to support dataflows from recorders submitting records to databases. However, we lack infrastructure dedicated to providing informative feedback to recorders in response to the data they have contributed. By developing this infrastructure, we can create a feedback loop leading to better data and more engaged data providers. This work builds on automated, personalised feedback delivered by email to butterfly recorders through the MyDECIDE programme in 2021 (run as part of the DECIDE project 2020-2021).

The Recorder Feedback Controller App provides a standalone application that interacts with other recording platforms (such as Indicia platforms like iRecord and iNaturalist). It is developed in Python using the Flask app framework. Its main purpose is for user management and dispatch of personalised feedback for biological recording.

App features:

 * Defines and hosts a database for holding information on:
    * Recorders - personal information, identifiers for recording platforms
    * Lists - the different types of feedback participants can subscribe to
    * Subscriptions - who has subscribed to what lists
    * Email history - logging who has received what feedback
 * Provides authenticated API endpoints as the main way of interacting with the database from an external service
    * Creating users
    * Subscribing / unsubscribing from lists
 * Some limited front-end functionality
    * Admin panel for user management and creating scheduled jobs for dispatching feedback
 * Interacts with the R code developed for generating the feedback items https://github.com/BiologicalRecordsCentre/recorder-feedback

See the wiki for detailed documentation: https://github.com/simonrolph/recorder-feedback-controller/wiki

## Development start up

### Prerequisites: Python, pip and virtualenv

This has been developed with Python 3.12 using pip for package management.
 * Python installation: https://www.python.org/downloads/ (or from the Software Centre if at UKCEH). Ensure it has been added to PATH environment variable https://realpython.com/add-python-to-path/
 * pip installation: https://pip.pypa.io/en/stable/installation/
 * Install virtualvenv: `python -m pip install virtualenv`

### Get the code

Clone repo and navigate inside folder:
```
git clone https://github.com/simonrolph/recorder-feedback-controller.git
cd recorder-feedback-controller
```
### Install packages

#### Option 1: Using virtualenv (preferred)

Create virtualenv
`python -m virtualenv venv`

Activate the virtualenv (not possible on UKCEH managed machines because of IT policies)
`venv\Scripts\activate` (windows)
`source venv/bin/activate` (unix)

#### Option 2: Not using virtualenv

Install packages using pip to the user library
`python -m pip install flask flask_mail apscheduler pyyaml`

### Configuring and launching Flask app

Create the config.py by copying from config_example.py and filling in details. Create a folder named `data`.
```
cp config_example.py config.py
mkdir data
```

This is the admin page log in username/password
```
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secret_password"
```

This is specific to the controller app and specifies if you want the API endpoints to be authenticated (by default you want this to be true but might help for testing if you turn it off). If it is `True` then it is authenitcated by a token you have provided here in the config for `SERVICE_API_TOKEN`. 
```
AUTHENTICATE_API = True
SERVICE_API_TOKEN = "complicated_token"
```

This is the configuration for Flask-mail,see https://flask-mail.readthedocs.io/en/latest/ for more details. Youcould use gmail as your SMTP service. Note that in UKCEH using smtp from a laptop via the VPN gets error `[WinError 10060] A connection attempt failed...` so make sure you're not on the VPN.

```
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT=465
MAIL_USE_TLS=False
MAIL_USE_SSL=True
MAIL_USERNAME='USERNAME'
MAIL_PASSWORD='PASSWORD'
MAIL_DEFAULT_SENDER='noreply@example.com'
```

Now you can run the app

```
python app.py
```

Then navigate to `http://127.0.0.1:5000/` taking you to the limited front end. Click on the link to go to the admin panel and enter the username (default: `admin`) and password you specified in `config.py`.

### Admin

The admin (`/admin`) page gives you some limited functionality for managing the database. It provides tables of lists, users, subscriptions (the links between lists and users), dispatch history, and feedback. There are links to unsubscribe a user from a list or submit test feedback for an item.

#### Useful pages

`/reset_data` will reset the database - remove this page if you're in production!

`/send_test_email` will send an email to the address specified in the config as `TEST_EMAIL`.

`/export_data` This will export the database as a csv

`/create_list` This will allow you to add a new list

## Deployment

### Posit connect

The app can be (in theory, I haven't actually got it working yet) deployed on a posit connect server. First install the `rsconnect-python` package. See https://docs.posit.co/rsconnect-python/ for documentation about the CLI. Main issue is that it still won't have publicly accessble endpoints unless public

`pip install rsconnect-python`

Create an API key from the Posit Connect website. Use the add command to store information about a Posit Connect server:

```
rsconnect add \
    --api-key my-api-key \
    --server https://connect.example.org \
    --name myserver
```

You can then deploy with the following command

```
rsconnect deploy flask ./ \
   --entrypoint app.py \
   --override-python-version 3.9.6 \
   static/style.css templates/create_list.html templates/index.html templates/send_test_email.html templates/submit_feedback.html templates/submitted_feedback.html templates/unsubscribe.html templates/unsubscribed.html config.py
```

Do command `rsconnect deploy flask` and it will show you all the options. 




## Notes

If you install new packages, add them to `requirements.txt` using `pip freeze > requirements.txt`
