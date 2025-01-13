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

#SERVER_URL = "http://89.223.125.229/predict" #server with AI,
SERVER_URL = "http://localhost:8000/predict" #if docker container with function exists
ADMIN_USER_ID = 1130761632  # ID of telegram account
ADMIN_USERNAME = "ne_sprashival" # Username of telegram account

def user_sqlinform(user, user_id):
    # Connection to data base (creates a file if it doesn't exist)
    conn = sqlite3.connect("User_data/users.db")
    cursor = conn.cursor()

    # Creates table, if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        user_id INTEGER NOT NULL UNIQUE
    )
    """)

    # Put data in table
    try:
        cursor.execute("INSERT INTO users (username, user_id) VALUES (?, ?)", (user, user_id))
        conn.commit()
        print(f"User {user} with ID {user_id} have been added to data base.")
    except sqlite3.IntegrityError:
        print(f"User with ID {user_id} already exist's in database.")

    # close connection
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


def resize_image(image, target_size=(640, 640)):
    """
    Resizes the image to the specified size (default 640x640).
    Returns the transformed image and the scale (scale_x, scale_y).
    """
    original_size = image.size
    img_resized = image.resize(target_size, Image.Resampling.LANCZOS)
    scale_x = target_size[0] / original_size[0]
    scale_y = target_size[1] / original_size[1]
    return img_resized, (scale_x, scale_y)

def draw_boxes_on_image(image, boxes, scale_factors):
    """
    Displays the original image with recalculated coordinates.
    """
    draw = ImageDraw.Draw(image)
    scale_x, scale_y = scale_factors
    res = []
    for box in boxes:
        # Recalculation of coordinates taking into account scaling
        x1, y1, x2, y2 = [box[0] / scale_x, box[1] / scale_y, box[2] / scale_x, box[3] / scale_y]
        res.append([x1, y1, x2, y2])
#        draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
    return res
#    return image

def send_image(img):
    """
    Sends an image to the FastAPI server after resizing.
    """
    original_image = img.copy()
    resized_image, scale_factors = resize_image(img)

    # Convert an image to a byte stream
    img_byte_arr = io.BytesIO()
    resized_image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # Sending the image to the server
    files = {"file": ("resized_image.jpg", img_byte_arr, "image/jpeg")}
    response = requests.post(SERVER_URL, files=files)

    # Processing the response
    if response.status_code == 200:
        result = response.json()
        boxes = result["boxes"]
        print("Segment coordinates (640x640): ", boxes)

        # Visualization of the original image with recalculated coordinates
#        image_with_boxes = draw_boxes_on_image(original_image, boxes, scale_factors)
#        plt.figure(figsize=(8, 8))
#        plt.imshow(image_with_boxes)
#        plt.axis("off")
#        plt.show()
#        print(boxes)
        return draw_boxes_on_image(original_image, boxes, scale_factors)
    else:
        print(f"Error {response.status_code}: {response.json()}")

def vigenere_encrypt(key, text): #function to encrypt text with key
    encrypted_text = []
    key = key.upper()
    key_length = len(key)

    for i, char in enumerate(text):
        if char.isalpha():  # Check if a character is a letter
            is_upper = char.isupper()
            shift = ord(key[i % key_length]) - ord('A')
            base = ord('A') if is_upper else ord('a')

            # Encrypting a symbol with shift
            encrypted_char = chr((ord(char) - base + shift) % 26 + base)
            encrypted_text.append(encrypted_char)
        else:
            # Leave the symbol unchanged if it is not a letter
            encrypted_text.append(char)

    return ''.join(encrypted_text)

def vigenere_decrypt(key, text): #function to decrypt text with key
    decrypted_text = []
    key = key.upper()
    key_length = len(key)

    for i, char in enumerate(text):
        if char.isalpha():  # Check if a character is a letter
            is_upper = char.isupper()
            shift = ord(key[i % key_length]) - ord('A')
            base = ord('A') if is_upper else ord('a')

            # Decoding a symbol taking into account the shift
            decrypted_char = chr((ord(char) - base - shift) % 26 + base)
            decrypted_text.append(decrypted_char)
        else:
            # Leave the symbol unchanged if it is not a letter
            decrypted_text.append(char)

    return ''.join(decrypted_text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id # stating user id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# stating current time
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")# stating unique timestamp
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")
    # Check if the file exists

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


        
    await update.message.reply_text(f'Hello {update.effective_user.first_name}!\nI am a smart chat-bot!\nList of commands: /list')

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")

    # Check if the file exists
    if os.path.exists(file_name):
    # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /start")
        print(f"Logs added to {file_name}.")
    else:
    # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /hello")
        print(f"File {file_name} created and logs saved.")
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")

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
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")


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
        
    await update.message.reply_text('Of course, here is the list of commands:\n/start - starts the bot\n/list - list of commands\n/hello - The bot responds with hello and your name in Telegram\n/buttons - you will get a buttons\n/qrcode [prompt] - Sends back to you QR code for yours prompt\n/graph [function] - you can send function and bot will send back graph of this function! (For example: 2x-3, sin(x), x^2)\n/polgraph [function] - you can send function and bot will send back graph of this function! (For example: r, sin(r), abs(r), or if you want a graph of heart: 2-2*sin(r)+sin(r)*(sqrt(abs(cos(r)))/(sin(r)+1.4)))\n/findphoto [prompt] - Will send you a google picture.\n/encrypt [key] [prompt] - Will encrypt prompt with key using Vigenere encryption\n/decrypt [key] [prompt] - Will decrypt prompt with key using Vigenere decryption\n/learn [function without slash] - Will tell you about the functions operation and its implementation (for example: facedetect, picture_size, encrypt)\n/feedback [text] - Please, write your feedback about the bot, or anything you would like us to add!\n\nOr you can send me picture, and I will reply what size it has in pixels and Using a specially trained neural network, it crops a photo to a persons face, if present.')

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("photo_received")
    user_id = update.effective_user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")


    # Check if the file exists
    if os.path.exists(file_name):
    # If file exists, append the new numbers to a new line
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id} sent a photo file_{user_id}_{unique_timestamp}")
        print(f"Logs added to {file_name}.")
    else:
    # If file doesn't exist, create the file and write the numbers
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id} sent a photo file_{user_id}_{unique_timestamp}")
        print(f"File {file_name} created and logs saved.")
    
    # Get the photo file (use the largest available size)
    photo = update.message.photo[-1]
    print(0)
    file = await photo.get_file()
    print(1)
    
    # Download the photo
    photo_data = await file.download_as_bytearray()

    # Load the image using PIL
    image = Image.open(io.BytesIO(photo_data))
    width, height = image.size
    boxes = send_image(image)
    file_name = f"User_photo/file_{user_id}_{unique_timestamp}.jpg"  # Unique filename based on file_id
    image.save(file_name)

    await update.message.reply_text(f'The photo size is {width}x{height} pixels.') #Sending back to user size of photo

    if boxes == []:
        await update.message.reply_text(f'No human recognized')
    else:
        await update.message.reply_text(f'I found {len(boxes)} person(s) here.')

    for element in boxes:
        # Округляем координаты вниз
        element = map(floor, element)
        print(element)
        cropped_image = image.crop(tuple(element))  # Обрезаем изображение

        # Сохраняем обрезанное изображение во временный буфер
        with io.BytesIO() as output:
            cropped_image.save(output, format="JPEG")  # Сохраняем как JPEG
            output.seek(0)  # Возвращаемся в начало потока

            # Отправляем обрезанное изображение пользователю
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=output)


    # Send the dimensions back to the user

async def qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    user_prompt = (update.message.text)[8:]
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")


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

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")

    # Log the command usage
    if os.path.exists(file_name):
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /buttons")
            print(f"Logs added to {file_name}.")
    else:
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /buttons")
            print(f"Logs added to {file_name}.")

    # Create buttons
    keyboard = [
        [InlineKeyboardButton("Button 1", callback_data='button1')],
        [InlineKeyboardButton("Button 2", callback_data='button2')],
        [InlineKeyboardButton("Button 3", callback_data='button3')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send message with inline buttons
    await update.message.reply_text('Choose an option:', reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
#    await query.answer()  #approvment of button

    #input check
    if query.data == 'button1':
        user_id = update.effective_user.id
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = f"User_data/{user_id}.txt"
        if os.path.exists(file_name):
            with open(file_name, 'a') as file:
                file.write(f"\n[{current_time}] {user_id} used button 1")
            print(f"Logs added to {file_name}.")
        else:
            with open(file_name, 'w') as file:
                file.write(f"[{current_time}] {user_id} used button 1")
            print(f"Logs added to {file_name}.")
            
        await query.edit_message_text(text="You pressed button 1!")
        
    elif query.data == 'button2':
        user_id = update.effective_user.id
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = f"User_data/{user_id}.txt"
        if os.path.exists(file_name):
            with open(file_name, 'a') as file:
                file.write(f"\n[{current_time}] {user_id} used button 2")
            print(f"Logs added to {file_name}.")
        else:
            with open(file_name, 'w') as file:
                file.write(f"[{current_time}] {user_id} used button 2")
            print(f"Logs added to {file_name}.")
            
        await query.edit_message_text(text="You pressed button 2!")
        
    elif query.data == 'button3':
        user_id = update.effective_user.id
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = f"User_data/{user_id}.txt"
        if os.path.exists(file_name):
            with open(file_name, 'a') as file:
                file.write(f"\n[{current_time}] {user_id} used button 3")
            print(f"Logs added to {file_name}.")
        else:
            with open(file_name, 'w') as file:
                file.write(f"[{current_time}] {user_id} used button 3")
            print(f"Logs added to {file_name}.")
            
        await query.edit_message_text(text="You pressed button 3!")

async def graph(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")


    # Log the command usage
    expression_text = ' '.join(context.args)  # Get the expression from the command arguments

    # Append log entry
    if os.path.exists(file_name):
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /graph {expression_text}")
        print(f"Logs added to {file_name}.")
    else:
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /graph {expression_text}")
        print(f"File {file_name} created and logs saved.")

    # Insert '*' between numbers and variables (e.g., convert '2x' to '2*x')
    expression_text = re.sub(r'(?<=[0-9])(?=[a-zA-Z])', '*', expression_text)

    # Parse the expression
    try:
        x = sp.symbols('x')  # Define the symbol 'x'
        expression = sp.sympify(expression_text)  # Parse the expression
    except (sp.SympifyError, ValueError):
        await update.message.reply_text("Invalid mathematical expression. Please try again.")
        return

    # Generate values for x and evaluate y based on the expression
    x_values = np.linspace(-10, 10, 400)
    try:
        # Use lambdify to convert sympy expression to a function that numpy can understand
        y_values = sp.lambdify(x, expression, "numpy")(x_values)
    except Exception as e:
        await update.message.reply_text("Error evaluating the expression. Please check the function syntax.")
        return

    # Plot the function with a dark theme
    plt.figure(facecolor='black')  # Set the figure background color
    plt.plot(x_values, y_values, color='cyan', label=f'y = {expression_text}')  # Plot in cyan color

    # Add coordinate axes
    plt.axhline(0, color='white', linewidth=0.8)  # x-axis in white
    plt.axvline(0, color='white', linewidth=0.8)  # y-axis in white

    # Title and labels with white color for visibility on dark background
    plt.title(f'Graph of y = {expression_text}', color='white')
    plt.xlabel('x', color='white')
    plt.ylabel('y', color='white')

    # Additional plot formatting
    plt.grid(True, color='gray')  # Set gridlines to gray
    plt.legend(facecolor='black', edgecolor='white', labelcolor='white', loc='upper right')  # Legend with white text
    plt.gca().set_facecolor("black")  # Set the axes background color to black
    plt.tick_params(colors='white')  # Set the tick labels color to white

    # Save the plot with a unique filename
    graph_filename = f"Graph_pic/graph_{username}_{unique_timestamp}.png"
    plt.savefig(graph_filename, facecolor='black')  # Ensure the background remains black when saved
    plt.close()

    # Send the plot back to the user
    with open(graph_filename, 'rb') as image_file:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file)

async def polgraph(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = f"User_data/{user_id}.txt"
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")

    # Log the command usage
    expression_text = ' '.join(context.args)  # Get the expression from the command arguments

    # Append log entry
    if os.path.exists(file_name):
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /polgraph {expression_text}")
        print(f"Logs added to {file_name}.")
    else:
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /polgraph {expression_text}")
        print(f"File {file_name} created and logs saved.")

    # Insert '*' between numbers and variables for multiplication (e.g., convert '2r' to '2*r')
    expression_text = re.sub(r'(?<=[0-9])(?=[a-zA-Z])', '*', expression_text)

    # Parse the expression
    try:
        r = sp.symbols('r')  # Define the symbol 'r' for polar coordinates
        expression = sp.sympify(expression_text)  # Parse the expression
    except (sp.SympifyError, ValueError):
        await update.message.reply_text("Invalid mathematical expression. Please try again.")
        return

    # Generate theta values
    theta_values = np.linspace(0, 2 * np.pi, 400)  # 0 to 2π
    try:
        # Use lambdify to convert sympy expression to a function that numpy can understand
        r_values = sp.lambdify(r, expression, "numpy")(theta_values)  # Evaluate r as a function of theta
    except Exception as e:
        await update.message.reply_text("Error evaluating the expression. Please check the function syntax.")
        return

    # Create polar plot
    plt.figure(facecolor='black')  # Set the figure background color
    ax = plt.subplot(111, projection='polar')  # Create polar subplot
    ax.plot(theta_values, r_values, color='cyan', label=f'r = {expression_text}')  # Plot in cyan color

    # Title and labels with white color for visibility on dark background
    ax.set_title(f'Polar Graph of r = {expression_text}', color='white')
    ax.set_xlabel('θ', color='white')  # Label for theta
    ax.set_ylabel('r', color='white')  # Label for r

    # Additional plot formatting
    ax.grid(color='gray')  # Set gridlines to gray
    ax.legend(facecolor='black', edgecolor='white', labelcolor='white', loc='upper right')  # Legend with white text
    ax.tick_params(colors='white')  # Set the tick labels color to white
    ax.set_facecolor("black")  # Set the axes background color to black

    # Save the polar plot with a unique filename
    polar_graph_filename = f"PGraph_pic/polar_graph_{username}_{unique_timestamp}.png"
    plt.savefig(polar_graph_filename, facecolor='black')  # Ensure the background remains black when saved
    plt.close()

    # Send the polar plot back to the user
    with open(polar_graph_filename, 'rb') as image_file:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file)


async def findphoto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datestamp = datetime.now().strftime("%Y%m%d")
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")


    # Log command usage
    file_name = f"User_data/{user_id}.txt"
    if os.path.exists(file_name):
        with open(file_name, 'a') as file:
            file.write(f"\n[{current_time}] {user_id}: /findphoto {context.args} [USER GOT foundphoto_{username}_{datestamp}.jpg]")
    else:
        with open(file_name, 'w') as file:
            file.write(f"[{current_time}] {user_id}: /findphoto {context.args} [USER GOT foundphoto_{username}_{datestamp}.jpg]")

    # Get the search query
    query = ' '.join(context.args)  # Join all arguments as a single search query
    if not query:
        await update.message.reply_text("Please provide a search query after the command.")
        return

    # Create an instance of GoogleImageCrawler
    google_crawler = GoogleImageCrawler(storage={'root_dir': 'G_pic'})

    # Crawl for images using the provided query
    google_crawler.crawl(keyword=query, max_num=1)

    # After crawling, check for the downloaded image and rename it
    original_image_pattern = 'G_pic/000001.jpg'  # Default filename from icrawler
    found_image_filename = f"foundphoto_{username}_{datestamp}.jpg"
    new_image_path = os.path.join('G_pic', found_image_filename)

    # Check if the original image exists and rename it
    if os.path.exists(original_image_pattern):
        # Ensure the new filename is unique
        counter = 1
        unique_new_image_path = new_image_path
        while os.path.exists(unique_new_image_path):
            unique_new_image_path = os.path.join('G_pic', f"foundphoto_{username}_{datestamp}_{counter}.jpg")
            counter += 1

        # Rename the image file
        os.rename(original_image_pattern, unique_new_image_path)

        # Send the found image back to the user
        with open(unique_new_image_path, 'rb') as image_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file)
    else:
        await update.message.reply_text("No image found for your query.")


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.username  # Getting the username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    feedback_text = ' '.join(context.args)  # Feedback text (after the command)
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")


    if not feedback_text:
        await update.message.reply_text(
            "Please provide your feedback after the command. Example: /feedback Your feedback here.")
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
                f"\n[{current_time}] {user_id}: /feedback {feedback_text[:100]}...")  # Logging the first 100 characters
        print(f"Logs added to {log_file_name}.")
    else:
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(
                f"[{current_time}] {user_id}: /feedback {feedback_text[:100]}...")  # Logging the first 100 characters
        print(f"Logs added to {log_file_name}.")

    await update.message.reply_text(f"Thank you for your feedback, {update.effective_user.first_name}!")


async def encrypt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.username  # Getting the username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    key = context.args[0] #Define the encryption key in a separate variable
    prompt = " ".join(context.args[1:]) #Define the text we want to encrypt
    print(context.args)
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")


    log_file_name = f"User_data/{user_id}.txt"
    if os.path.exists(log_file_name):
        with open(log_file_name, 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"\n[{current_time}] {user_id}: /encrypt {key} {prompt}")  #Logging if such a file already exists
        print(f"Logs added to {log_file_name}.")
    else:
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(
                f"[{current_time}] {user_id}: /encrypt {key} {prompt}")  #Logging if there is no such file
        print(f"Logs added to {log_file_name}.")

    await update.message.reply_text(f"This is what happened after the Vigenere encryption:\n{vigenere_encrypt(key, prompt)}")


async def decrypt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.username  # Getting the username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    key = context.args[0] #Define the encryption key in a separate variable
    prompt = " ".join(context.args[1:]) #Define the text we want to encrypt
    print(context.args)
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")


    log_file_name = f"User_data/{user_id}.txt"
    if os.path.exists(log_file_name):
        with open(log_file_name, 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"\n[{current_time}] {user_id}: /decrypt {key} {prompt}")  #Logging if such a file already exists
        print(f"Logs added to {log_file_name}.")
    else:
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(
                f"[{current_time}] {user_id}: /decrypt {key} {prompt}")  #Logging if there is no such file
        print(f"Logs added to {log_file_name}.")

    await update.message.reply_text(f"This is what happened after deciphering Vigenere:\n{vigenere_decrypt(key, prompt)}")


async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.username  # Getting the username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    print(context.args)
    usernome = update.effective_user.username
    user_sqlinform(usernome, user_id)

    # getting user_id by username
    user_idi = get_user_id_by_username(usernome)
    if user_idi is not None:
        print(f"ID of user '{usernome}': {user_idi}")
    else:
        print(f"user {usernome} doesn't exists")

    if context.args != []:
        prompt = context.args[0]
    else:
        await update.message.reply_text(f"Sure! Just type /learn [FUNCTION WITHOUT SLASH]")

    log_file_name = f"User_data/{user_id}.txt"
    if os.path.exists(log_file_name):
        with open(log_file_name, 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"\n[{current_time}] {user_id}: /learn {prompt}")  #Logging if such a file already exists
        print(f"Logs added to {log_file_name}.")
    else:
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(
                f"[{current_time}] {user_id}: /learn {prompt}")  #Logging if there is no such file
        print(f"Logs added to {log_file_name}.")

    if prompt == "start" or prompt == "list" or prompt == "hello" or prompt == "buttons" or prompt == "feedback" or prompt == "learn":
        await update.message.reply_text(f"This is a fairly simple function that does not use any additional features")
    elif prompt == "qrcode":
        await update.message.reply_text(f"This function uses an additional library in python, qrcode. It renders any prompt as a qrcode, after which we send you this image")
    elif prompt == "graph" or prompt == "polgraph":
        await update.message.reply_text(f"I'm so glad you asked about this function! It uses matplotlib and numpy libraries. We create 2 arrays, in one of which we take an independent variable, and the second we compose as a function of each element of the first array. After that we place the points on the coordinate plane, connect them, draw them and send them to you, our beloved users!")
    elif prompt == "findphoto":
        await update.message.reply_text(f"This function first processes your prompt, then parses the photo and sends the one that suits you")
    elif prompt == "encrypt":
        await update.message.reply_text(f"I'm so glad you asked about this function! This function uses a type of encryption and decryption called the Vigenère cipher. It is an example of a polyalphabetic cipher, in which each character of the text is encrypted using different shifts depending on the characters of the key.\n\nThe Vigenère cipher was invented in the 16th century and was considered unbroken for a long time because its resistance to frequency analysis is much higher than that of monoalphabetic ciphers (such as the Caesar cipher).\n\nThe encryption works like this:\nEach letter of the text is shifted a certain number of positions, depending on the corresponding letter of the key.\nFor example, if the text to be encrypted is HELLO and the key is KEY:\nThe letters of the key are repeated: KEYKE (so that the length matches the text).\nThe shifts are determined by the letters of the key: K = 10, E = 4, Y = 24 (counting from A).\nThe letters of the text are shifted:\nH (shift 10) -> R\nE (shift 4) -> I\nL (shift 24) -> J\nand so on")
    elif prompt == "decrypt":
        await update.message.reply_text(f"I'm so glad you asked about this function! This function uses a type of encryption and decryption called the Vigenère cipher. It is an example of a polyalphabetic cipher, in which each character of the text is encrypted using different shifts depending on the characters of the key.\n\nThe Vigenère cipher was invented in the 16th century and was considered unbroken for a long time because its resistance to frequency analysis is much higher than that of monoalphabetic ciphers (such as the Caesar cipher).\n\nDecryption occurs as follows:\nTo decrypt the text, each character is shifted back by the number of positions determined by the corresponding letter of the key.\nFor example, to decrypt the cipher RIJVS with the key KEY:\nDecrypt each letter using the reverse shift determined by the key:\nR (shift -10) -> H\nI (shift -4) -> E\nand so on")
    elif prompt == "facedetect":
        await update.message.reply_text(f"This feature uses a specially trained model that segments the photo, then crops it based on the segmentation and sends you back only the person's face")
    elif prompt == "picture_size":
        await update.message.reply_text(f"This function downloads the image, analyzes it, records the resolution, and then we return it to you.")
    else:
        await update.message.reply_text(f"Sorry, there is no such function in the bot. Perhaps you made a typo, or are looking for a non-existent function")
    #Find out the function the user wants to know about and send a suitable response

'''
async def facedetect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"This feature is currently under development and will be added very soon. We will be waiting for you soon!")
'''

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
        db_file = "User_data/users.db"
        if os.path.exists(db_file):
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(db_file, 'rb'))
            print(f"Admin {username} accessed the database file.")
        else:
            await update.message.reply_text("Database file not found.")
            print(f"Database file '{db_file}' not found.")
    else:
        await update.message.reply_text("This function is for admins only.")
        print(f"Unauthorized access attempt by user {username} (ID: {user_id}).")



user_sqlinform("testuser", 12)

# test of getting user_id by username
usernome = "testuser"
user_id = get_user_id_by_username(usernome)
if user_id is not None:
    print(f"ID of user '{usernome}': {user_id}")
else:
    print(f"user {usernome} doesn't exists")

# test on real account
usernome = "ne_sprashival"
user_id = get_user_id_by_username(usernome)
if user_id is not None:
    print(f"ID of user '{usernome}': {user_id}")
else:
    print(f"user {usernome} doesn't exists")

all_users = get_all_users()
print("All users:", all_users)

#app = ApplicationBuilder().token("7332049578:AAE5V5jZbLgfPXiLzJoyqZ8cXViNmi3Y0Sk").build() #Connecting to the bot using token
app = ApplicationBuilder().token("7539063885:AAGayqU81bbGmUxkdvh0m8bw9Byf4edn0Xs").build() #Connecting to the bot using token
app.add_handler(CommandHandler("hello", hello)) #Creating handler for command with function

app.add_handler(CommandHandler("ping", ping)) #Creating handler for command with function

app.add_handler(CommandHandler("start", start)) #Creating handler for command with function

app.add_handler(CommandHandler("list", list)) #Creating handler for command with function

app.add_handler(MessageHandler(filters.PHOTO, photo_handler)) #Creating handler to define the picture size without additional command

app.add_handler(CommandHandler("qrcode", qr_code)) #Creating handler for command with function

app.add_handler(CommandHandler("buttons", buttons)) #Creating handler for command with function

app.add_handler(CommandHandler("graph", graph)) #Creating handler for command with function

app.add_handler(CommandHandler("polgraph", polgraph)) #Creating handler for command with function

app.add_handler(CommandHandler("findphoto", findphoto)) #Creating handler for command with function

app.add_handler(CommandHandler("feedback", feedback)) #Creating handler for command with function

app.add_handler(CommandHandler("encrypt", encrypt)) #Creating handler for command with function

app.add_handler(CommandHandler("decrypt", decrypt)) #Creating handler for command with function

app.add_handler(CommandHandler("learn", learn)) #Creating handler for command with function

#app.add_handler(CommandHandler("facedetect", facedetect)) #Creating handler for command with function

app.add_handler(CommandHandler("getusers", admin_check))

app.add_handler(CallbackQueryHandler(button_callback))

app.run_polling()

#:)
