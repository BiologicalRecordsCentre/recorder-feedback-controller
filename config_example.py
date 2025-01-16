# config.py
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secret_password"

# Service
AUTHENTICATE_API = True
SERVICE_API_TOKEN = "complicated_token"

# Dispatch method
DISPATCH_METHOD = 'email' # 'email

# if DISPATCH_METHOD = email then set these
# Flask-Mail
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT=465
MAIL_USE_TLS=False
MAIL_USE_SSL=True
MAIL_USERNAME='USERNAME'
MAIL_PASSWORD='PASSWORD'
MAIL_DEFAULT_SENDER='noreply@example.com'

TEST_EMAIL='youemail@example.com'