# Recorder Feedback Controller App

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
`python -m virvualenv venv`

Activate the virtualenv (not possible on UKCEH managed machines because of IT policies)
`venv\Scripts\activate` (windows)
`source venv/bin/activate` (unix)

#### Option 2: Not using virtualenv

Install packages using pip to the user library
`python -m pip install flask flask_mail apscheduler pyyaml`

### Lauch Flask app

Create the config.py by copying from config_example.py and filling in details. Create a folder named `data`. Run the app
```
cp config_example.py config.py
mkdir data
python app.py
```
Then navigate to `http://127.0.0.1:5000/` taking you to the limited front end. Click on the link to go to the admin panel and enter the username and password you specified in `config.py`.

### Hosting R code

This app calls R code which generates the html feedback items before dispatch. Here I want to make a feedback list called 'weekly-report'. Navigate to the R directory, clone the R code repository then rename the folder to 'weekly-report' (or whatever you wish to call your list).

```
cd R
git clone https://github.com/BiologicalRecordsCentre/recorder-feedback
ren recorder-feedback weekly-report
```

Follow the set-up instructions located here: https://biologicalrecordscentre.github.io/recorder-feedback/
