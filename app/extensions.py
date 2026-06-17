from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from app.database import db

bcrypt = Bcrypt()
login_manager = LoginManager()

# Default login redirect target
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
