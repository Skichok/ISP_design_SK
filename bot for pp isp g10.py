import math
import telegram
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode  # For message formatting
import logging  # For debugging and logging errors
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw
import io
import os
from datetime import datetime, timedelta #for datestamp
import qrcode #to create qrcode
import matplotlib.pyplot as plt #to create graphs
import numpy as np #to create graphs
import sympy as sp #to parse mathematical expressions
import imageio
import re
#from google.generativeai import GenerateText
from icrawler.builtin import GoogleImageCrawler #to parse photoes
from math import floor
#import sqlite3
from USERS_DATA_DB_WORK_FILE import CalendarBotDB
import openpyxl
from openpyxl import Workbook
import pandas as pd
import asyncio  # To ensure proper async execution


db = CalendarBotDB()
ADMIN_USER_ID = 1130761632  # ID of telegram account
ADMIN_USERNAME = "ne_sprashival" # Username of telegram account


def check_time(type: str, time: str) -> bool:
    parts = time.split(":")
    if len(parts) != 3:
        return False

    try:
        Hours, Minutes, Seconds = map(int, parts)
    except ValueError:
        return False

    if not (0 <= Hours <= 23 and 0 <= Minutes <= 59 and 0 <= Seconds <= 59):
        return False

    return True

def check_day(type: str, day: str) -> bool:
    try:
        # Try to convert the string to an integer (number of minutes)
        dayt = int(day)
        # Check if the number is non-negative and does not exceed 14 days (20160 minutes)
        return 1 <= dayt <= 7
    except ValueError:
        # If conversion fails (e.g., the input is not a number), return False
        return False


def check_stamp(type: str, stamp: str) -> bool:
    try:
        # Try to convert string in datetime object
        dt = datetime.strptime(stamp, "%H:%M:%S %d.%m.%y")
        # Check, if sucess
        return True
    except ValueError:
        # If not, return false
        return False

def check_duration(type: str, duration: str) -> bool:
    try:
        # Try to convert the string to an integer (number of minutes)
        minutes = int(duration)
        # Check if the number is non-negative and does not exceed 14 days (20160 minutes)
        return 0 <= minutes <= 20160
    except ValueError:
        # If conversion fails (e.g., the input is not a number), return False
        return False

def check_notify_before(type: str, notify_before: str) -> bool:
    try:
        # Try to convert the string to an integer (number of minutes)
        minutes = int(notify_before)
        # Check if the number is non-negative and does not exceed 60 minutes
        return 0 <= minutes <= 60
    except ValueError:
        # If conversion fails (e.g., the input is not a number), return False
        return False

def is_single_event_unique(user_id: int, stamp) -> bool:
    res = True
    for item in db.get_user_events_single(user_id=user_id):
        if stamp not in item:
            continue
        else:
            res = False
    return res

def is_recurring_event_unique(user_id: int, day, time) -> bool:
    res = True
    print(user_id, day, time)
    print(type(day), type(time))
    day = int(day)
    for item in db.get_user_events_recurring(user_id=user_id):
        print(item)
        print(item[1], item[2])
        print(type(item[1]), type(item[2]))
        if item[1] == day and item[2] == time:
            res = False
        else:
            continue
    print(res)
    return res

def get_language(user_id) -> str:
    return db.language(user_id=user_id)


def graph_stats(stats_dict, theme="light", language="en", pic_path="stats_chart.png"):
    """
    Renders a bar graph from stats_dict, with customizable theme and language.

    :param stats_dict: dict, where keys are days of the week (0-6) and values are event counts
    :param theme: str, either "light" or "dark" (default is "light")
    :param language: str, either "en" (default) or "fr"
    :param pic_path: str, the path to save the generated graph
    """
    # Days of the week in English and French
    days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    # Titles and labels in English and French
    titles = {
        "en": {"title": "Weekly Event Statistics", "x_label": "Days of the Week", "y_label": "Number of Events"},
        "fr": {"title": "Statistiques des événements hebdomadaires", "x_label": "Jours de la semaine",
               "y_label": "Nombre d'événements"}
    }

    # Select labels and titles based on language
    days_labels = days_en if language == "en" else days_fr
    title = titles[language]["title"]
    x_label = titles[language]["x_label"]
    y_label = titles[language]["y_label"]

    # Map day indices to labels
    labels = [days_labels[day] for day in stats_dict.keys()]
    values = [de for de in stats_dict.values()]

    # Set up theme-based colors
    if theme == "light":
        bg_color = "white"
        bar_color = "black"
        edge_color = "black"
    else:  # dark theme
        bg_color = "black"
        bar_color = "white"
        edge_color = "white"

    # Create the plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color=bar_color, edgecolor=edge_color)  # Set edge color for bars

    # Customize appearance
    plt.gca().set_facecolor(bg_color)  # Background color
    plt.xticks(color=bar_color, fontsize=12)
    plt.yticks(color=bar_color, fontsize=12)
    plt.xlabel(x_label, fontsize=14, color=bar_color)
    plt.ylabel(y_label, fontsize=14, color=bar_color)
    plt.title(title, fontsize=16, color=bar_color)

    # Adjust layout and save the plot
    plt.tight_layout()
    plt.savefig(pic_path, facecolor=bg_color)
    plt.close()
    return

def shift_events_to_excel(data1, data2, tablename, language="en"):
    # Ensure the data is valid and both arrays exist
    if not data1 and not data2:
        if language == "fr":
            print("Les deux tableaux de données sont vides.")
        else:
            print("Both data arrays are empty.")
        return

    # Combine both data arrays
    all_events = data1 + data2

    # Create a new Excel file
    wb = Workbook()
    ws = wb.active
    ws.title = "Schedule"

    # Column headers
    headers = ["Time"] + [(datetime.now() + timedelta(days=i)).strftime("%d.%m.%y") for i in range(14)]
    ws.append(headers)

    # Sort events by time
    all_events.sort(key=lambda x: x[2])

    # Create rows based on the event times
    time_rows = {}
    for event in all_events:
        if len(event) == 6:
            event_time = event[2]
        elif len(event) == 5:
            event_datetime = datetime.strptime(event[1], "%H:%M:%S %d.%m.%y")
            if event_datetime.date() <= datetime.now().date():
                continue
            event_time = event_datetime.strftime("%H:%M:%S")
        else:
            continue

        if event_time not in time_rows:
            time_rows[event_time] = ["" for _ in range(14)]

    # Fill events into rows
    for event in all_events:
        if len(event) == 6:
            event_day_offset = event[1] - 2  # Day of the week (2=Monday)
            event_time = event[2]
            event_name = event[3]
        elif len(event) == 5:
            event_datetime = datetime.strptime(event[1], "%H:%M:%S %d.%m.%y")
            event_day_offset = (event_datetime - datetime.now()).days
            if event_datetime.date() <= datetime.now().date():
                continue
            event_time = event_datetime.strftime("%H:%M:%S")
            event_name = event[2]
        else:
            continue

        if 0 <= event_day_offset < 14:
            time_rows[event_time][event_day_offset] = event_name

    # Write rows to Excel
    for time, events in sorted(time_rows.items()):
        ws.append([time] + events)

    # Save the file
    file_path = f"./User_data/tables/{tablename}.xlsx"
    wb.save(file_path)
    if language == "fr":
        print(f"Fichier enregistré avec succès à l'emplacement : {file_path}")
    else:
        print(f"File successfully saved at: {file_path}")

import os
from datetime import datetime, timedelta
from openpyxl import Workbook
from telegram import Update
from telegram.ext import ContextTypes
import matplotlib.pyplot as plt
import pandas as pd

def shift_events(data1, data2, tablename, language="en"):
    if not data1 and not data2:
        print("Both data arrays are empty." if language == "en" else "Les deux tableaux de données sont vides.")
        return

    all_events = data1 + data2
    wb = Workbook()
    ws = wb.active
    ws.title = "Schedule"
    headers = ["Time"] + [(datetime.now() + timedelta(days=i)).strftime("%d.%m.%y") for i in range(14)]
    ws.append(headers)
    all_events.sort(key=lambda x: x[2])
    time_rows = {}

    for event in all_events:
        if len(event) == 6:
            event_time = event[2]
        elif len(event) == 5:
            event_datetime = datetime.strptime(event[1], "%H:%M:%S %d.%m.%y")
            if event_datetime.date() <= datetime.now().date():
                continue
            event_time = event_datetime.strftime("%H:%M:%S")
        else:
            continue

        if event_time not in time_rows:
            time_rows[event_time] = ["" for _ in range(14)]

    for event in all_events:
        if len(event) == 6:
            event_day_offset = event[1] - 2
            event_time = event[2]
            event_name = event[3][:5]
        elif len(event) == 5:
            event_datetime = datetime.strptime(event[1], "%H:%M:%S %d.%m.%y")
            event_day_offset = (event_datetime - datetime.now()).days
            if event_datetime.date() <= datetime.now().date():
                continue
            event_time = event_datetime.strftime("%H:%M:%S")
            event_name = event[2][:5]
        else:
            continue

        if 0 <= event_day_offset < 14:
            time_rows[event_time][event_day_offset] = event_name

    for time, events in sorted(time_rows.items()):
        ws.append([time] + events)

    file_path = f"./User_data/tables/{tablename}.xlsx"
    wb.save(file_path)
    print(f"File successfully saved at: {file_path}" if language == "en" else f"Fichier enregistré avec succès à l'emplacement : {file_path}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    language = get_language(user_id)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    if len(db.get_user(user_id=user_id)) == 0:
        db.add_user(user_id=user_id, username=usernome)
    else:
        pass

    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /start")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /start")
        print(f"File {file_name} created and logs saved.")

    start_msg = {
        "en": "Hello! I am your smart assistant.\nUse /list to see available commands.",
        "fr": "Bonjour! Je suis votre assistant intelligent.\nUtilisez /list pour voir les commandes disponibles."
    }

    await update.message.reply_text(start_msg.get(language, start_msg["en"]))

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    language = get_language(user_id)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username

    # Check if the file exists
    if os.path.exists(file_name):
    # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /hello")
        print(f"Logs added to {file_name}.")
    else:
    # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /hello")
        print(f"File {file_name} created and logs saved.")

    hello_msg = {
        "en": "Hello",
        "fr": "Bonjour"
    }

    await update.message.reply_text(hello_msg.get(language, hello_msg["en"])+f", {update.effective_user.first_name}!")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username

    # Check if the file exists
    if os.path.exists(file_name):
    # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /ping")
        print(f"Logs added to {file_name}.")
    else:
    # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /ping")
        print(f"File {file_name} created and logs saved.")
        
    await update.message.reply_text('pong')

async def list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    language = get_language(user_id)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = f"User_data/{user_id}.txt"

    # Check if the file exists
    if os.path.exists(file_name):
    # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /list")
        print(f"Logs added to {file_name}.")
    else:
    # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /list")
        print(f"File {file_name} created and logs saved.")

    list_msg = {
        "en": "Available commands:\n/start - start the bot\n/hello - greet the bot\n/language [en/fr] - change language\n/theme [light/dark] - change theme\n/adds <HH:MM:SS> <DD.MM.YY> <duration in minutes> <notify before minutes> <description> – add a new single event\n/deletes <HH:MM:SS> <DD.MM.YY> – remove an existing single event\n/changes <HH:MM:SS> <DD.MM.YY> <new duration in minutes> <new notify before minutes> <new description> – modify an existing event by providing its original time and date, then updating the details\n/addr <number-of-day> <HH:MM:SS> <duration in minutes> <notify before minutes> <description> - add a new recurring event\n/deleter <number-of-day> <HH:MM:SS> - delete recurring event\n/changer <number-of-day> <HH:MM:SS> <new duration in minutes> <new notify before minutes> <new description> - change recurring event\n/mytables - get image of your plan for next two weeks\n/stats - get a graph of the number of recurring events per day\n/statx - get logs and schedule for 2 weeks in excel format\n/feedback <feedback text> - sends feedback to the developers\n(Admin functions: /ping, /getusers)",
        "fr": "Commandes disponibles:\n/start - démarrer le bot\n/hello - saluer le bot\n/language [en/fr] - changer de langue\n/theme [clair/foncé] - changer de thème\n/adds <HH:MM:SS> <DD.MM.YY> <durée en minutes> <notification avant en minutes> <description> – ajouter un nouvel événement\n/deletes <HH:MM:SS> <DD.MM.YY> – supprimer un événement existant\n/changes <HH:MM:SS> <DD.MM.YY> <nouvelle durée en minutes> <nouvelle notification avant en minutes> <nouvelle description> – Modifier un événement existant en indiquant son heure et sa date d'origine, puis en mettant à jour les détails\n/addr <numéro de jour> <HH:MM:SS> <durée en minutes> <notifier avant minutes> <description> - ajouter un nouvel événement récurrent\n/deleter <nombre-de-jours> <HH:MM:SS> - supprimer l'événement récurrent\n/changer <numéro de jour> <HH:MM:SS> <nouvelle durée en minutes> <nouvelle notification avant minutes> <nouvelle description> - modifier l'événement récurrent\n/mytables - obtenez une image de votre plan pour les deux prochaines semaines\n/stats - obtenir un graphique du nombre d'événements récurrents par jour\n/statx - Obtenez les journaux et le calendrier pour 2 semaines au format Excel\n/feedback <texte du feedback> - envoyer les commentaires aux développeurs\n(Fonctions d'administration : /ping, /getusers)"
    }

    await update.message.reply_text(list_msg.get(language, list_msg["en"]))

async def qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    user_prompt = (update.message.text)[8:]
    usernome = update.effective_user.username


    # Check if the file exists
    if os.path.exists(file_name):
    # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /qrcode {user_prompt} [USER GOT qr_{user_id}_{unique_timestamp}.png]")
        print(f"Logs added to {file_name}.")
    else:
    # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /qrcode {user_prompt} [USER GOT qr_{user_id}_{unique_timestamp}.png]")
        print(f"File {file_name} created and logs saved.")


    img_usr = qrcode.make(user_prompt)  

    type(img_usr)  # qrcode.image.pil.PilImage
    img_usr.save(f"QR_image/qr_{user_id}_{unique_timestamp}.png")
    img_byte_arr = io.BytesIO()
    img_usr.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)  # Go to the start of the BytesIO object
    
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img_byte_arr)

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.username  # Getting the username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    feedback_text = ' '.join(context.args)  # Feedback text (after the command)
    language = get_language(user_id)  # Get user’s preferred language

    if not feedback_text:
        feedback_msg = {
            "en": "Please provide your feedback after the command. Example: /feedback Your feedback here.",
            "fr": "Veuillez fournir vos commentaires après la commande. Exemple: /feedback Votre commentaire ici."
        }
        await update.message.reply_text(feedback_msg.get(language, feedback_msg["en"]))
        return

    file_name = f"User_data/feedback_{user_name}_{unique_timestamp}.txt"

    # Save the feedback to a new file with utf-8 encoding
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(f"[{current_time}] Feedback from {user_name} ({user_id}):\n{feedback_text}\n")
    print(f"Feedback saved to {file_name}.")

    # Logging the use of the /feedback command with utf-8 encoding
    log_file_name = f"User_data/{user_id}.txt"
    if os.path.exists(log_file_name):
        with open(log_file_name, 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"\n[{current_time}] {user_id}: /feedback {feedback_text[:50]}...")  # Logging the first 100 characters
        print(f"Logs added to {log_file_name}.")
    else:
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(
                f"[{current_time}] {user_id}: /feedback {feedback_text[:50]}...")  # Logging the first 100 characters
        print(f"Logs added to {log_file_name}.")

    feedback_response = {
        "en": f"Thank you for your feedback, {update.effective_user.first_name}!",
        "fr": f"Merci pour vos commentaires, {update.effective_user.first_name}!"
    }

    await update.message.reply_text(feedback_response.get(language, feedback_response["en"]))

#
# async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user_id = update.effective_user.id
#     user_name = update.effective_user.username  # Getting the username
#     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
#     print(context.args)
#     usernome = update.effective_user.username
#
#
#     if context.args != []:
#         prompt = context.args[0]
#     else:
#         await update.message.reply_text(f"Sure! Just type /learn [FUNCTION WITHOUT SLASH]")
#
#     log_file_name = f"User_data/{user_id}.txt"
#     if os.path.exists(log_file_name):
#         with open(log_file_name, 'a', encoding='utf-8') as log_file:
#             log_file.write(
#                 f"\n[{current_time}] {user_id}: /learn {prompt}")  #Logging if such a file already exists
#         print(f"Logs added to {log_file_name}.")
#     else:
#         with open(log_file_name, 'w', encoding='utf-8') as log_file:
#             log_file.write(
#                 f"[{current_time}] {user_id}: /learn {prompt}")  #Logging if there is no such file
#         print(f"Logs added to {log_file_name}.")
#
#     if prompt == "start" or prompt == "list" or prompt == "hello" or prompt == "buttons" or prompt == "feedback" or prompt == "learn":
#         await update.message.reply_text(f"This is a fairly simple function that does not use any additional features")
#     elif prompt == "qrcode":
#         await update.message.reply_text(f"This function uses an additional library in python, qrcode. It renders any prompt as a qrcode, after which we send you this image")
#     elif prompt == "graph" or prompt == "polgraph":
#         await update.message.reply_text(f"I'm so glad you asked about this function! It uses matplotlib and numpy libraries. We create 2 arrays, in one of which we take an independent variable, and the second we compose as a function of each element of the first array. After that we place the points on the coordinate plane, connect them, draw them and send them to you, our beloved users!")
#     elif prompt == "findphoto":
#         await update.message.reply_text(f"This function first processes your prompt, then parses the photo and sends the one that suits you")
#     elif prompt == "encrypt":
#         await update.message.reply_text(f"I'm so glad you asked about this function! This function uses a type of encryption and decryption called the Vigenère cipher. It is an example of a polyalphabetic cipher, in which each character of the text is encrypted using different shifts depending on the characters of the key.\n\nThe Vigenère cipher was invented in the 16th century and was considered unbroken for a long time because its resistance to frequency analysis is much higher than that of monoalphabetic ciphers (such as the Caesar cipher).\n\nThe encryption works like this:\nEach letter of the text is shifted a certain number of positions, depending on the corresponding letter of the key.\nFor example, if the text to be encrypted is HELLO and the key is KEY:\nThe letters of the key are repeated: KEYKE (so that the length matches the text).\nThe shifts are determined by the letters of the key: K = 10, E = 4, Y = 24 (counting from A).\nThe letters of the text are shifted:\nH (shift 10) -> R\nE (shift 4) -> I\nL (shift 24) -> J\nand so on")
#     elif prompt == "decrypt":
#         await update.message.reply_text(f"I'm so glad you asked about this function! This function uses a type of encryption and decryption called the Vigenère cipher. It is an example of a polyalphabetic cipher, in which each character of the text is encrypted using different shifts depending on the characters of the key.\n\nThe Vigenère cipher was invented in the 16th century and was considered unbroken for a long time because its resistance to frequency analysis is much higher than that of monoalphabetic ciphers (such as the Caesar cipher).\n\nDecryption occurs as follows:\nTo decrypt the text, each character is shifted back by the number of positions determined by the corresponding letter of the key.\nFor example, to decrypt the cipher RIJVS with the key KEY:\nDecrypt each letter using the reverse shift determined by the key:\nR (shift -10) -> H\nI (shift -4) -> E\nand so on")
#     elif prompt == "facedetect":
#         await update.message.reply_text(f"This feature uses a specially trained model that segments the photo, then crops it based on the segmentation and sends you back only the person's face")
#     elif prompt == "picture_size":
#         await update.message.reply_text(f"This function downloads the image, analyzes it, records the resolution, and then we return it to you.")
#     else:
#         await update.message.reply_text(f"Sorry, there is no such function in the bot. Perhaps you made a typo, or are looking for a non-existent function")
#     #Find out the function the user wants to know about and send a suitable response
#
# '''
# async def facedetect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(f"This feature is currently under development and will be added very soon. We will be waiting for you soon!")
# '''

async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    if os.path.exists(log_file_name):
        with open(log_file_name, 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"\n[{current_time}] {user_id}: /getusers [ADMIN ONLY COMMAND]")  #Logging if such a file already exists
        print(f"Logs added to {log_file_name}.")
    else:
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(
                f"[{current_time}] {user_id}: /getusers [ADMIN ONLY COMMAND]")  #Logging if there is no such file
        print(f"Logs added to {log_file_name}.")

    # Check if the user is an admin
    if user_id == ADMIN_USER_ID and username == ADMIN_USERNAME:
        # Check if the database file exists
        db_file = db.dbpath
        if os.path.exists(db_file):
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(db_file, 'rb'))
            print(f"Admin {username} accessed the database file.")
        else:
            await update.message.reply_text("Database file not found.")
            print(f"Database file '{db_file}' not found.")
    else:
        await update.message.reply_text("This function is for admins only.")
        print(f"Unauthorized access attempt by user {username} (ID: {user_id}).")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id)
    language = db.language(user_id)


    if os.path.exists(log_file_name):
        with open(log_file_name, 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"\n[{current_time}] {user_id}: /stats")  # Logging if such a file already exists
        print(f"Logs added to {log_file_name}.")
    else:
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(
                f"[{current_time}] {user_id}: /stats")  # Logging if there is no such file
        print(f"Logs added to {log_file_name}.")

    graph_stats(stats_dict=stats_dict, theme=theme, language=language, pic_path=file_path)
    with open(file_path, 'rb') as image_file:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file)

async def theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    current_theme = db.theme(user_id=user_id)
    new_theme = "dark" if current_theme == "light" else "light"
    db.switch_theme(user_id=user_id, theme=new_theme)

    theme_response = {
        "en": f"Theme changed from {current_theme} to {new_theme}!",
        "fr": f"Thème a changé de {current_theme} à {new_theme}!"
    }

    await update.message.reply_text(theme_response.get(language, theme_response["en"]))

#    await update.message.reply_text(f"Theme changed from {current_theme} to {new_theme}")

    if os.path.exists(log_file_name):
        with open(log_file_name, 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"\n[{current_time}] {user_id}: /theme [{theme} -> {new_theme}]")  # Logging if such a file already exists
        print(f"Logs added to {log_file_name}.")
    else:
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(
                f"[{current_time}] {user_id}: /theme [{theme} -> {new_theme}]")  # Logging if there is no such file
        print(f"Logs added to {log_file_name}.")

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    current_language = db.language(user_id=user_id)
    new_language = "fr" if current_language == "en" else "en"  # Пример смены языка с "en" на "fr" и наоборот
    db.change_language(user_id=user_id, language=new_language)
    if new_language == "en":
        await update.message.reply_text(f"Language changed from {current_language} to {new_language}")
        if os.path.exists(log_file_name):
            with open(log_file_name, 'a', encoding='utf-8') as log_file:
                log_file.write(
                    f"\n[{current_time}] {user_id}: /language [fr -> en]")  # Logging if such a file already exists
            print(f"Logs added to {log_file_name}.")
        else:
            with open(log_file_name, 'w', encoding='utf-8') as log_file:
                log_file.write(
                    f"[{current_time}] {user_id}: /language [fr -> en]")  # Logging if there is no such file
            print(f"Logs added to {log_file_name}.")
    else:
        await update.message.reply_text(f"Langue modifiée depuis {current_language} à {new_language}")
        if os.path.exists(log_file_name):
            with open(log_file_name, 'a', encoding='utf-8') as log_file:
                log_file.write(
                    f"\n[{current_time}] {user_id}: /language [en -> fr]")  # Logging if such a file already exists
            print(f"Logs added to {log_file_name}.")
        else:
            with open(log_file_name, 'w', encoding='utf-8') as log_file:
                log_file.write(
                    f"[{current_time}] {user_id}: /language [en -> fr]")  # Logging if there is no such file
            print(f"Logs added to {log_file_name}.")

async def add_single_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # adds single event
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    file_name = f"User_data/{user_id}.txt" # log file
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    user_inf = (update.message.text)[6:] # Сначала идет время ивента, в формате XX:XX:XX YY.YY.YY после чего продолжительность в минутах, одно число, оповестить за сколько минут, тоже одно число, после описание события
    tmp = False
    notify_before = 0
    stamp = 0
    duration = 0
    description = " "
    if len(user_inf.split(" ")) >= 5:
        stamp = user_inf.split(" ")[0] + " " + user_inf.split(" ")[1]
        duration = user_inf.split(" ")[2]
        notify_before = user_inf.split(" ")[3]
        description = " ".join(user_inf.split(" ")[4:])
        tmp = True
        print(stamp)
        print(duration)
        print(notify_before)
        print(description)
        print(user_inf)

    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /adds {user_inf}")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /adds {user_inf}")
        print(f"File {file_name} created and logs saved.")

    if check_stamp("single", stamp=stamp) == True and check_duration("single", duration=duration) == True and tmp == True and check_notify_before("single", notify_before) == True:
        if is_single_event_unique(user_id=user_id, stamp=stamp) == True:
            db.add_single_event(user_id=user_id, event_timestamp=stamp, description=description, duration_minutes=description, notify_before_minutes=notify_before)
            if language == "en":
                await update.message.reply_text(
                    f"Successfully added event {description} on {stamp}")
            else:
                await update.message.reply_text(
                    f"L'événement {description} a été ajouté avec succès pour l'heure {stamp}")

        else:
            if language == "en":
                await update.message.reply_text(f"Sorry, it looks like you already have something in that timestamp, please delete or change it first")
            else:
                await update.message.reply_text(f"Désolé, il semble que vous ayez déjà quelque chose dans cet horodatage, veuillez d'abord le supprimer ou le modifier.")

    else:
        if language == "en":
            await update.message.reply_text(
                f"Sorry, wrong input format. Input format: /adds HH:MM:SS DD.MM.YY N M DESCRIPTION\nWhere\nN - event time\nM - how long before the event to notify (<= 60 min)")
        else:
            await update.message.reply_text(
                f"Désolé, le format d'entrée est incorrect. Format d'entrée : /adds HH:MM:SS JJ.MM.AA N M DESCRIPTION\nOù\nN - heure de l'événement\nM - combien de temps avant l'événement faut-il notifier (<= 60 min)")

        # /adds

async def add_recurring_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # 2 = monday
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    file_name = f"User_data/{user_id}.txt"  # log file
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    user_inf = (update.message.text)[
               6:]  # Сначала идет день (цифра) ивента, после время в формате XX:XX:XX после чего продолжительность в минутах, одно число, оповестить за сколько минут, тоже одно число, после описание события
    tmp = False
    notify_before = 0
    day = 0
    time = " "
    duration = 0
    description = " "
    if len(user_inf.split(" ")) >= 5:
        day = user_inf.split(" ")[0] # 1 = sunday, 2 = monday, 3 = tuesday, ..., 7 = saturday
        time = user_inf.split(" ")[1]
        duration = user_inf.split(" ")[2]
        notify_before = user_inf.split(" ")[3]
        description = " ".join(user_inf.split(" ")[4:])
        tmp = True
        print(day)
        print(time)
        print(duration)
        print(notify_before)
        print(description)
        print(user_inf)

    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /addr {user_inf}")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /addr {user_inf}")
        print(f"File {file_name} created and logs saved.")

    if check_day(type="recurring", day=day) == True and check_time(type="recurring", time=time) and check_duration("recurring", duration=duration) == True and check_notify_before(type="recurring", notify_before=notify_before) == True:
        if is_recurring_event_unique(user_id=user_id, day=day, time=time) == True:
            db.add_recurring_event(user_id=user_id, day_of_week=day, event_time=time, description=description, duration_minutes=duration, notify_before_minutes=notify_before)
            if language == "en":
                await update.message.reply_text(
                    f"Successfully added event {description} on {time}")
            else:
                await update.message.reply_text(
                    f"L'événement {description} a été ajouté avec succès pour l'heure {time}")
        else:
            if language == "en":
                await update.message.reply_text(f"Sorry, it looks like you already have something in that timestamp, please delete or change it first")
            else:
                await update.message.reply_text(f"Désolé, il semble que vous ayez déjà quelque chose dans cet horodatage, veuillez d'abord le supprimer ou le modifier.")
    else:
        if language == "en":
            await update.message.reply_text(
                f"Sorry, wrong input format. Input format: /addr DAY HH.MM.SS N M DESCRIPTION\nWhere\nDAY - number from 1 to 7 (1 = sunday, 2 = monday ...)\nN - event time\nM - how long before the event to notify (<= 60 min)")
        else:
            await update.message.reply_text(
                f"Désolé, format d'entrée incorrect. Format attendu : /addr JOUR HH.MM.SS N M DESCRIPTION\nOù\nJOUR - numéro de 1 à 7 (1 = dimanche, 2 = lundi ...)\nN - durée de l'événement\nM - délai de notification avant l'événement (≤ 60 min)")

# /addr - add recurring event

async def delete_single_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # deletes single event
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    file_name = f"User_data/{user_id}.txt"  # log file
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    user_inf = (update.message.text)[
               9:]  # Сначала идет время ивента, в формате XX:XX:XX YY.YY.YY после чего продолжительность в минутах, одно число, оповестить за сколько минут, тоже одно число, после описание события
    tmp2 = False
    notify_before = 0
    stamp = 0
    duration = 0
    description = " "
    if len(user_inf.split(" ")) >= 2:
        stamp = user_inf.split(" ")[0] + " " + user_inf.split(" ")[1]
        #duration = user_inf.split(" ")[2]
        #notify_before = user_inf.split(" ")[3]
        #description = " ".join(user_inf.split(" ")[4:])
        tmp2 = True
        print(stamp)
        print(duration)
        print(notify_before)
        print(description)
        print(user_inf)

    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /deletes {user_inf}")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /deletes {user_inf}")
        print(f"File {file_name} created and logs saved.")

    if check_stamp("single", stamp=stamp) == True and tmp2 == True:
        if is_single_event_unique(user_id=user_id, stamp=stamp) == True:
            if language == "en":
                await update.message.reply_text(
                    f"Sorry, it doesn't look like you have single event at {stamp}")
            else:
                await update.message.reply_text(
                    f"Désolé, il semble que vous n'ayez aucun événement à {stamp}")

        else:
            db.delete_single_event(user_id=user_id, event_timestamp=stamp)
            if language == "en":
                await update.message.reply_text(
                    f"Successfully deleted single event on {stamp}")
            else:
                await update.message.reply_text(
                    f"Événement unique supprimé avec succès le {stamp}")

    else:
        if language == "en":
            await update.message.reply_text(
                f"Sorry, wrong input format. Input format: /deletes HH:MM:SS DD.MM.YY")
        else:
            await update.message.reply_text(
                f"Désolé, le format d'entrée est incorrect. Format d'entrée : /deletes HH:MM:SS JJ.MM.AA")
    # /deletes

async def delete_recurring_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # 2 = monday
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    file_name = f"User_data/{user_id}.txt"  # log file
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    user_inf = (update.message.text)[
               9:]  # Сначала идет день (цифра) ивента, после время в формате XX:XX:XX
    tmp = False
    notify_before = 0
    day = 0
    time = " "
    duration = 0
    description = " "
    if len(user_inf.split(" ")) >= 5:
        day = user_inf.split(" ")[0]  # 1 = sunday, 2 = monday, 3 = tuesday, ..., 7 = saturday
        time = user_inf.split(" ")[1]
        #duration = user_inf.split(" ")[2]
        #notify_before = user_inf.split(" ")[3]
        #description = " ".join(user_inf.split(" ")[4:])
        tmp = True
        print(day)
        print(time)
        print(duration)
        print(notify_before)
        print(description)
        print(user_inf)

    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /deleter {user_inf}")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /deleter {user_inf}")
        print(f"File {file_name} created and logs saved.")

    if check_day(type="recurring", day=day) == True and check_time(type="recurring", time=time):
        if is_recurring_event_unique(user_id=user_id, day=day, time=time) == False:
            db.delete_recurring_event(user_id=user_id, day_of_week=day, event_time=time)
            if language == "en":
                await update.message.reply_text(
                    f"Successfully deleted event {description} on {time}")
            else:
                await update.message.reply_text(
                    f"L'événement {description} a été supprimé avec succès le {time}")
        else:
            if language == "en":
                await update.message.reply_text(
                    f"Sorry, it looks like you don't have anything in that timestamp, please delete or change it first")
            else:
                await update.message.reply_text(
                    f"Désolé, il semble que vous n'ayez aucune chose dans cet horodatage, veuillez d'abord le supprimer ou le modifier.")
    else:
        if language == "en":
            await update.message.reply_text(
                f"Sorry, wrong input format. Input format: /deleter DAY HH.MM.SS\nWhere\nDAY - number from 1 to 7 (1 = sunday, 2 = monday ...)")
        else:
            await update.message.reply_text(
                f"Désolé, format d'entrée incorrect. Format attendu : /deleter JOUR HH.MM.SS\nOù\nJOUR - numéro de 1 à 7 (1 = dimanche, 2 = lundi ...)")

    #deletes recurring event

async def get_user_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # drawing/showing as a previewable file user plan as a table and sends back to user
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    file_name = f"User_data/{user_id}.txt"  # log file
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    recurring_events = db.get_user_events_recurring(user_id=user_id)
    single_events = db.get_user_events_single(user_id=user_id)
    all_events = recurring_events + single_events

    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /mytables")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /mytables")
        print(f"File {file_name} created and logs saved.")

    if not all_events:
        msg = "You have not created a schedule yet. Please create one." if language == "en" else "Vous n'avez pas encore créé de planning. Veuillez en créer un."
        await update.message.reply_text(msg)
        return

    dates = [(datetime.now() + timedelta(days=i)).strftime("%d.%m.%y") for i in range(14)]
    # Фильтруем time_slots: только корректное время формата HH:MM:SS
    time_slots = sorted(
        set(event[2] for event in all_events if len(event) >= 5 and isinstance(event[2], str) and ":" in event[2]))

    # Создаем пустую таблицу с датами как колонками
    data = {date: ["" for _ in time_slots] for date in dates}

    for event in all_events:
        if len(event) == 6:
            event_day_offset = event[1] - 2
            event_time = event[2]
            event_name = event[3][:5]
        elif len(event) == 5:
            event_datetime = datetime.strptime(event[1], "%H:%M:%S %d.%m.%y")
            event_day_offset = (event_datetime - datetime.now()).days
            event_time = event_datetime.strftime("%H:%M:%S")
            event_name = event[2][:5]
        else:
            continue

        if 0 <= event_day_offset < 14:
            if event_time in time_slots:
                data[dates[event_day_offset]][time_slots.index(event_time)] = event_name
            else:
                print(f"Warning: Skipping event '{event_name}' at {event_time}, not found in time_slots!")

    df = pd.DataFrame(data, index=time_slots)
    fig, ax = plt.subplots(figsize=(10, 6))
    if theme == "dark":
        bg_color = "black"
        text_color = "white"
        cell_color = "black"  # Фон ячеек
        edge_color = "white"  # Цвет границ
    else:
        bg_color = "white"
        text_color = "black"
        cell_color = "white"
        edge_color = "black"

    # Создаем изображение
    fig, ax = plt.subplots(figsize=(10, 6))

    # Устанавливаем фон графика
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    # Создаем таблицу
    table = ax.table(cellText=df.values, colLabels=df.columns, rowLabels=df.index,
                     cellLoc='center', loc='center')

    # Настраиваем размеры шрифта
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # Устанавливаем цвета для ячеек и границ
    for key, cell in table.get_celld().items():
        cell.set_text_props(color=text_color)  # Цвет текста
        cell.set_facecolor(cell_color)  # Фон ячейки
        cell.set_edgecolor(edge_color)  # Цвет границ

    # Скрываем оси
    ax.axis("off")

    # Сохраняем изображение
    file_path = f"./User_data/tables/preview_{user_id}.png"
    plt.savefig(file_path, bbox_inches='tight', facecolor=bg_color)
    plt.close()

    await update.message.reply_photo(photo=open(file_path, 'rb'))


# /mytables

async def change_single_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # change time/name/notify_before for recurring event
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    file_name = f"User_data/{user_id}.txt"  # log file
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    user_inf = (update.message.text)[
               9:]  # Сначала идет время ивента, в формате XX:XX:XX YY.YY.YY после чего продолжительность в минутах, одно число, оповестить за сколько минут, тоже одно число, после описание события
    tmp = False
    notify_before = 0
    stamp = 0
    duration = 0
    description = " "
    if len(user_inf.split(" ")) >= 5:
        stamp = user_inf.split(" ")[0] + " " + user_inf.split(" ")[1]
        duration = user_inf.split(" ")[2]
        notify_before = user_inf.split(" ")[3]
        description = " ".join(user_inf.split(" ")[4:])
        tmp = True
        print(stamp)
        print(duration)
        print(notify_before)
        print(description)
        print(user_inf)

    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /changes {user_inf}")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /changes {user_inf}")
        print(f"File {file_name} created and logs saved.")

    if check_stamp("single", stamp=stamp) == True and check_duration("single",
                                                                     duration=duration) == True and tmp == True and check_notify_before(
            "single", notify_before) == True:
        if is_single_event_unique(user_id=user_id, stamp=stamp) == True:
            if language == "en":
                await update.message.reply_text(
                    f"Sorry, it doesn't seems like you have any single events on these time, use this command to add it:\n\n/adds {stamp} {duration} {notify_before} {description}")
            else:
                await update.message.reply_text(
                    f"Désolé, il ne semble pas que vous ayez un événement à ce moment-là. Utilisez cette commande pour l'ajouter :\n\n/adds {stamp} {duration} {notify_before} {description}")

        else:
            db.delete_single_event(user_id=user_id, event_timestamp=stamp)
            db.add_single_event(user_id=user_id, event_timestamp=stamp, description=description, duration_minutes=description, notify_before_minutes=notify_before)
            if language == "en":
                await update.message.reply_text(
                    f"Successfully changed event {description} on {stamp}")
            else:
                await update.message.reply_text(
                    f"Événement {description} à {stamp} modifié avec succès")

    else:
        if language == "en":
            await update.message.reply_text(
                f"Sorry, wrong input format. Input format: /adds HH:MM:SS DD.MM.YY N M DESCRIPTION\nWhere\nN - event time\nM - how long before the event to notify (<= 60 min)")
        else:
            await update.message.reply_text(
                f"Désolé, le format d'entrée est incorrect. Format d'entrée : /adds HH:MM:SS JJ.MM.AA N M DESCRIPTION\nOù\nN - heure de l'événement\nM - combien de temps avant l'événement faut-il notifier (<= 60 min)")


# /changes

async def change_recurring_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # change time/name/notify_before for recurring event
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/pic/stats_{user_id}_{unique_timestamp}.png"
    file_name = f"User_data/{user_id}.txt"  # log file
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    user_inf = (update.message.text)[
               9:]  # Сначала идет день (цифра) ивента, после время в формате XX:XX:XX после чего новая продолжительность в минутах, одно число, новое значение оповестить за сколько минут, тоже одно число, после новое описание события
    tmp = False
    notify_before = 0
    day = 0
    time = " "
    duration = 0
    description = " "
    if len(user_inf.split(" ")) >= 5:
        day = user_inf.split(" ")[0]  # 1 = sunday, 2 = monday, 3 = tuesday, ..., 7 = saturday
        time = user_inf.split(" ")[1]
        duration = user_inf.split(" ")[2]
        notify_before = user_inf.split(" ")[3]
        description = " ".join(user_inf.split(" ")[4:])
        tmp = True
        print(day)
        print(time)
        print(duration)
        print(notify_before)
        print(description)
        print(user_inf)

    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /changer {user_inf}")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /changer {user_inf}")
        print(f"File {file_name} created and logs saved.")

    if check_day(type="recurring", day=day) == True and check_time(type="recurring", time=time):
        if is_recurring_event_unique(user_id=user_id, day=day, time=time) == False:
            db.delete_recurring_event(user_id=user_id, day_of_week=day, event_time=time)
            db.add_recurring_event(user_id=user_id, day_of_week=day, event_time=time, description=description, duration_minutes=time, notify_before_minutes=notify_before)
            if language == "en":
                await update.message.reply_text(
                    f"Successfully changed event {description} on {time}")
            else:
                await update.message.reply_text(
                    f"L'événement {description} a été modifié avec succès le {time}")
        else:
            if language == "en":
                await update.message.reply_text(
                    f"Sorry, it looks like you don't have anything in that timestamp, you can use this command to add recurring event:\n/addr {day} {time} {duration} {notify_before} {description}")
            else:
                await update.message.reply_text(
                    f"Désolé, il semble que vous n'ayez rien dans cet horodatage, vous pouvez utiliser cette commande pour ajouter un événement récurrent:\n/addr {day} {time} {duration} {notify_before} {description}")
    else:
        if language == "en":
            await update.message.reply_text(
                f"Sorry, wrong input format. Input format: /changer DAY HH.MM.SS N M DESCRIPTION\nWhere\nDAY - number from 1 to 7 (1 = sunday, 2 = monday ...)\nN - event time\nM - how long before the event to notify (<= 60 min)")
        else:
            await update.message.reply_text(
                f"Désolé, format d'entrée incorrect. Format attendu : /changer JOUR HH.MM.SS N M DESCRIPTION\nOù\nJOUR - numéro de 1 à 7 (1 = dimanche, 2 = lundi ...)\nN - durée de l'événement\nM - délai de notification avant l'événement (≤ 60 min)")

    # /changer

async def user_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: #sends excel file of table and log file
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    log_file_name = f"User_data/{user_id}.txt"
    file_path = f"./User_data/tables/table_{user_id}_{unique_timestamp}.xlsx"
    stats_dict = db.stats(user_id=user_id)
    theme = db.theme(user_id=user_id)
    language = db.language(user_id=user_id)
    file_name = f"User_data/{user_id}.txt"


    if os.path.exists(file_name):
        # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /statx")
        print(f"Logs added to {file_name}.")
    else:
        # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /statx")
        print(f"File {file_name} created and logs saved.")

    print(db.get_user_events_recurring(user_id=user_id), db.get_user_events_single(user_id=user_id))
    shift_events_to_excel(data1=db.get_user_events_recurring(user_id=user_id), data2=db.get_user_events_single(user_id=user_id), tablename=f"table_{user_id}_{unique_timestamp}", language=language)
    if not os.path.exists(file_path):
        if language == "en":
            await update.message.reply_text(f"You have not created a schedule yet. Please create one.")
        else:
            await update.message.reply_text(f"Vous n'avez pas encore créé de planning. Veuillez en créer un.")
    else:
        if language == "en":
            await update.message.reply_text(f"Here is your 2 week schedule in excel spreadsheets:")
        else:
            await update.message.reply_text(f"Voici votre programme de 2 semaines sur Excel:")
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, 'rb'))

    if language == "en":
        await update.message.reply_text(f"Here are your logs for the entire time you've been using the bot:")
    else:
        await update.message.reply_text(f"Voici votre journal d'activité pendant la durée de votre utilisation du bot:")
    await context.bot.send_document(chat_id=update.effective_chat.id, document=open(f"./User_data/{user_id}.txt"))


async def ai_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # last to do
    pass # uses DeepSeek/Ollama locally to help user to create his own time table on week (including recurring events)


async def check_streak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass # shows to user his current streak of using bot


#app = ApplicationBuilder().token("7332049578:AAE5V5jZbLgfPXiLzJoyqZ8cXViNmi3Y0Sk").build() #Connecting to the bot using token

app = ApplicationBuilder().token("7915205789:AAEQc4SVq-wd3VHlWgKK-VcQy8mCtDbNYY8").build() #Connecting to the bot using token

app.add_handler(CommandHandler("hello", hello)) #Creating handler for command with function

app.add_handler(CommandHandler("ping", ping)) #Creating handler for command with function

app.add_handler(CommandHandler("start", start)) #Creating handler for command with function

app.add_handler(CommandHandler("list", list)) #Creating handler for command with function

app.add_handler(CommandHandler("qrcode", qr_code)) #Creating handler for command with function

app.add_handler(CommandHandler("feedback", feedback)) #Creating handler for command with function

#app.add_handler(CommandHandler("learn", learn)) #Creating handler for command with function

#app.add_handler(CommandHandler("facedetect", facedetect)) #Creating handler for command with function

app.add_handler(CommandHandler("getusers", admin_check))

app.add_handler(CommandHandler("stats", stats))

app.add_handler(CommandHandler("theme", theme))

app.add_handler(CommandHandler("language", change_language))

app.add_handler(CommandHandler("adds", add_single_event))

app.add_handler(CommandHandler("deletes", delete_single_event))

app.add_handler(CommandHandler("deleter", delete_recurring_event))

app.add_handler(CommandHandler("addr", add_recurring_event))

app.add_handler(CommandHandler("mytables", get_user_plan))

app.add_handler(CommandHandler("changes", change_single_event))

app.add_handler(CommandHandler("changer", change_recurring_event))

app.add_handler(CommandHandler("statx", user_data))

app.add_handler(CommandHandler("aihelp", ai_help))

app.run_polling()

# :)
