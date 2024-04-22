# Recorder Feedback Controller App

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
