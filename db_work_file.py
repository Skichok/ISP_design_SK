import math
import telegram
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw
import io
import os
from datetime import datetime #for datestamp
import qrcode #to create qrcode
import matplotlib.pyplot as plt #to create graphs
import numpy as np #to create graphs
import sympy as sp #to parse mathematical expressions
import imageio
import re
from icrawler.builtin import GoogleImageCrawler #to parse photoes
from math import floor
import sqlite3

def user_sqlinform(user, user_id, action="ADD"):
    # Connection to the database (creates a file if it doesn't exist)
    conn = sqlite3.connect("User_data/users.db")
    cursor = conn.cursor()

    # Creates table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        user_id INTEGER NOT NULL UNIQUE
    )
    """)

    if action == "ADD":
        # Add data to the table
        try:
            cursor.execute("INSERT INTO users (username, user_id) VALUES (?, ?)", (user, user_id))
            conn.commit()
            print(f"User {user} with ID {user_id} has been added to the database.")
        except sqlite3.IntegrityError:
            print(f"User with ID {user_id} already exists in the database.")

    elif action == "REMOVE":
        # Remove user from the table
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"User with ID {user_id} has been removed from the database.")
        else:
            print(f"User with ID {user_id} does not exist in the database.")

    else:
        print("Invalid action. Use 'ADD' to add a user or 'REMOVE' to delete a user.")

    # Close the connection
    conn.close()


def get_user_id_by_username(username):
    # connection to database
    conn = sqlite3.connect("User_data/users.db")
    cursor = conn.cursor()

    # Executing a SQL query
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()  # Getting one data

    # closing connection
    conn.close()

    # returning ID of user, if it exists
    if result:
        return result[0]
    else:
        print(f"User with username '{username}' doesn't exist.")
        return None


def get_all_users():
    # Connecting to database
    conn = sqlite3.connect("User_data/users.db")
    cursor = conn.cursor()

    # Execute SQL Query to Get All Users
    cursor.execute("SELECT username FROM users")
    results = cursor.fetchall()  # Get all records as a list of tuples

    # Closing connection
    conn.close()

    # Convert a list of tuples to a list of strings
    users = [row[0] for row in results]
    return users


all_users = get_all_users()
print("All users:", " | ".join(all_users))

for usernome in all_users:
    user_id = get_user_id_by_username(usernome)
    if user_id is not None:
        print(f"ID of user '{usernome}': {user_id}")
    else:
        print(f"user {usernome} doesn't exists")
print(type(user_id))

otd = input("Do you want to add users manualy? (y/n): ")

if otd == "y":
    print("To finish write 'FINISH'")
    usernime = input("Write username: ")
    if usernime == "FINISH":
        pass
    else:
        usor_idi = input("Write user id: ")
    while usernime != "FINISH" and usor_idi != "FINISH":
        usor_idi = int(usor_idi)
        user_sqlinform(usernime, usor_idi)
        print("Success")
        usernime = input("Write username: ")
        if usernime == "FINISH":
            break
        usor_idi = input("Write user id: ")
    print("OK, here is new database:")
    all_users = get_all_users()
    print("All users:", " | ".join(all_users))

    for usernome in all_users:
        user_id = get_user_id_by_username(usernome)
        if user_id is not None:
            print(f"ID of user '{usernome}': {user_id}")
        else:
            print(f"user {usernome} doesn't exists")


else:
    pass

otd = input("Do you want to remove users manualy? (y/n): ")

if otd == "y":
    print("To finish write 'FINISH'")
    usernime = input("Write username: ")
    if usernime == "FINISH":
        pass
    else:
        usor_idi = input("Write user id: ")
    while usernime != "FINISH" and usor_idi != "FINISH":
        usor_idi = int(usor_idi)
        user_sqlinform(usernime, usor_idi, "REMOVE")
        print("Success")
        usernime = input("Write username: ")
        if usernime == "FINISH":
            break
        usor_idi = input("Write user id: ")
    print("OK, here is new database:")
    all_users = get_all_users()
    print("All users:", " | ".join(all_users))

    for usernome in all_users:
        user_id = get_user_id_by_username(usernome)
        if user_id is not None:
            print(f"ID of user '{usernome}': {user_id}")
        else:
            print(f"user {usernome} doesn't exists")


else:
    pass

print("Program finished")