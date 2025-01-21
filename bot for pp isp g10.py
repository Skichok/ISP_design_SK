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
#from google.generativeai import GenerateText
from icrawler.builtin import GoogleImageCrawler #to parse photoes
from math import floor
#import sqlite3
from USERS_DATA_DB_WORK_FILE import CalendarBotDB

db = CalendarBotDB()
ADMIN_USER_ID = 1130761632  # ID of telegram account
ADMIN_USERNAME = "ne_sprashival" # Username of telegram account
def get_language(user_id):
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
        "en": "Available commands:\n/start - start the bot\n/hello - greet the bot\n/language [en/fr] - change language\n/theme [light/dark] - change theme\nqrcode <prompt> - generate qr code for prompt\n/stats - get a recurring plans schedule for the week\n/feedback <feedback text> - sends feedback to the developers\n(Admin functions: /ping, /getusers)",
        "fr": "Commandes disponibles:\n/start - démarrer le bot\n/hello - saluer le bot\n/language [en/fr] - changer de langue\n/theme [clair/foncé] - changer de thème\nqrcode <prompt> - générer un code qr pour l'invite\n/stats - obtenez un calendrier de plans récurrents pour la semaine\n/feedback <texte du feedback> - prend en compte les commentaires puis le développeur\n(Fonctions d'administration : /ping, /getusers)"
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

    await update.message.reply_text(f"Theme changed from {current_theme} to {new_theme}")

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

app.run_polling()

# :)
