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
`python -m virvualenv venv`

Activate the virtualenv (not possible on UKCEH managed machines because of IT policies)
`venv\Scripts\activate` (windows)
`source venv/bin/activate` (unix)

#### Option 2: Not using virtualenv

Install packages using pip to the user library
`python -m pip install flask flask_mail apscheduler pyyaml`

### Initial set up

Create the config.py by copying from config_example.py and filling in details. Create a folder named `data`. Run the app
```
cp config_example.py config.py
mkdir data
python app.py
```
Then navigate to `http://127.0.0.1:5000/`
