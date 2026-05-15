
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
