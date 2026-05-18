config.py

1
import os
Imports Python's built-in os module. It helps your code interact with the operating system — especially for reading environment variables.
2
from dotenv import load_dotenv
Imports the load_dotenv() function from the python-dotenv package. This function reads your .env file.
3
load_dotenv()
Very Important Line
This tells your app: "Go read the .env file and load all the variables (like SECRET_KEY and DATABASE_URL) into the environment."
Without this line, your app cannot read the .env file.
4
class Config:
Creates a configuration class. This is a clean way to store all settings for your Flask app.
5
SECRET_KEY = os.getenv("SECRET_KEY")
Reads the SECRET_KEY from the .env file and assigns it to this variable.
Used for security (sessions, cookies, password hashing, etc.).
6
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
Reads the DATABASE_URL from .env and tells SQLAlchemy (your database tool) where your PostgreSQL database is located and how to connect to it.
7
SQLALCHEMY_TRACK_MODIFICATIONS = False
Turns off a feature that tracks every change to objects. It saves memory and improves performance. You should almost always set this to False.

user.py
db.Model: This class represents one table in the database
db.Column(...): Defines one column (field) in the table
primary_key=True: Unique identifier for each row
unique=True: No two users can have same username or email
nullable=False: This field must have a value
default='waiter': New users will be waiters by default
UserMixin: Adds useful methods like is_authenticated, is_active, get_id() needed for login
password_hash: Stores secure version of password (never plain text)
set_password(): Used when creating new user or changing password
check_password(): Used during login to verify password

from app import db # Import the SQLAlchemy database instance
from flask_login import UserMixin # Gives extra features for login (like is_authenticated, etc.)
from datetime import datetime # To handle date and time
from werkzeug.security import generate_password_hash, check_password_hash

# Tools to securely hash and check passwords

class User(UserMixin, db.Model): # Create a class that represents a table in the database
**tablename** = 'users' # Name of the table in PostgreSQL database

    id = db.Column(db.Integer, primary_key=True)
    # Every user will have a unique ID (auto-increment)

    username = db.Column(db.String(80), unique=True, nullable=False)
    # Username must be unique and cannot be empty

    email = db.Column(db.String(120), unique=True, nullable=False)
    # Email must also be unique

    password_hash = db.Column(db.String(256), nullable=False)
    # We store hashed password (NEVER store plain password)

    full_name = db.Column(db.String(100), nullable=False)
    # Full name of the person (Admin, Chef, Waiter, etc.)

    role = db.Column(db.String(20), nullable=False, default='waiter')
    # Important: Defines user type → admin, chef, waiter, store_manager

    is_active = db.Column(db.Boolean, default=True)
    # Whether the account is active or disabled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Automatically saves the time when user was created

    # Password Methods

    def set_password(self, password):
        """Hash the password before saving to database"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if entered password matches the stored hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """How the user object is displayed when printed"""
        return f"<User {self.username} ({self.role})>"

db = SQLAlchemy(): Creates a database object (extension)
migrate = Migrate(): For handling database changes (creating/updating tables)
login_manager: Manages user login sessions
socketio: For realtime features (alerts, kitchen updates)
create_app(): App Factory Pattern – Best way to create Flask app. Makes testing and scaling easier.
app.config.from_object('config.Config'): Loads settings from config.py (secret key, database URL, etc.)
with app.app_context(): Temporarily activates the app so we can import models safely
app.register_blueprint(auth): Connects the authentication routes to the main app
@login_manager.user_loader: Tells Flask-Login how to load a user from the database using their ID

Blueprint('auth', __name__): Creates a mini-application (blueprint) for authentication. Helps keep code organized.
url_prefix='/auth': All routes in this file will start with /auth (e.g., /auth/login, /auth/register)
flash(): Shows temporary messages (success, danger, info) to the user
login_user(user): Logs the user in and creates a session
logout_user(): Logs the user out
current_user: Represents the currently logged-in user
@login_required: Protects a route — user must be logged in to access it