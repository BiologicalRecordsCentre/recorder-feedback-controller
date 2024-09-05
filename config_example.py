# config.py
API_KEY = 'secret_key'
ADMIN_PASSWORD = "secret_password"

# Service
AUTHENTICATE_API = True
SERVICE_API_TOKEN = "complicated_token"

# Dispatch method
DISPATCH_METHOD = 'email' # 'email or 'indicia_notifications'

# if DISPATCH_METHOD = email then set these
# Flask-Mail
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME='USERNAME'
MAIL_PASSWORD='PASSWORD'
MAIL_DEFAULT_SENDER='noreply@example.com'
TEST_MODE = True
TEST_EMAIL='youemail@example.com'

# if DISPATCH_METHOD = 'indicia_notifications'
INDICIA_USER = "user"
INDICIA_SECRET = "secret"

#R
RSCRIPT_PATH = "C:/Path/To/R/R-4.x.x/bin/Rscript.exe"