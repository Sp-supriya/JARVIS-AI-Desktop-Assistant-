import pyttsx3
import datetime
import speech_recognition as sr
import wikipedia
import webbrowser
import os
import smtplib
import pywhatkit
import warnings
import requests
import csv
import re
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import socket
import sys
from voice_password import password 
# Ensure proper encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')

# Ignore SSL warnings
warnings.simplefilter('ignore', InsecureRequestWarning)

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# File to store user inputs
csv_file = 'user_actions.csv'

# Action Mapping
action_map = {
    'open youtube': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'play song on youtube': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    'search wikipedia': [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    'open google': [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    'open vs code': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    'send email': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    'open stackoverflow': [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    'schedule meeting': [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    'open email': [0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    'power off': [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
}
reverse_action_map = {tuple(v): k for k, v in action_map.items()}

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def wishMe():
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        speak("Good Morning!")
    elif hour >= 12 and hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I am Jarvis. Please tell me how may I help you")

def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 0.7
        audio = r.listen(source)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"user said: {query}\n")
    except Exception as e:
        print(e)
        print("Say that again please...")
        return "None"
    return query

def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email)

def spell_email():
    email_parts = []
    speak("Please spell out the email address in one go or letter by letter.")
    speak("Say 'at' for '@', 'dot' for '.', and numbers like 'one' for 1.")
    
    number_map = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
    }

    while True:
        captured_input = takeCommand().lower().strip()  # Ensure no extra spaces
        print(f"Captured input: '{captured_input}'")  # Debugging
        
        if not captured_input or captured_input == "none":
            speak("I didn't catch that. Please try again.")
            continue

        # Direct check for "done"
        if "done" in captured_input.split() or captured_input == "done":
            print("Detected 'done', exiting input loop.")  # Debugging
            break
        else:
            email_parts=[]

        # Tokenize input into words or characters
        tokens = captured_input.split()
        print(f"Tokens extracted: {tokens}")  # Debugging

        for token in tokens:
            if token == "done":  # Break immediately if "done" is found in tokens
                print("Detected 'done' in tokens, exiting.")  # Debugging
                return "".join(email_parts)
            elif token == "at":
                email_parts.append("@")
            elif token == "dot":
                email_parts.append(".")
            elif token in number_map:
                email_parts.append(number_map[token])  # Convert spoken numbers to digits
            elif re.match(r"^\d+$", token):  # Capture multi-digit numbers like "10", "123"
                email_parts.append(token)
            elif re.match(r"^[a-z0-9]$", token):  # Alphanumeric validation for single characters
                email_parts.append(token)
            else:
                speak(f"Invalid input: {token}. Please try again.")
                continue

        speak("Do you want to continue or say 'done' if finished.")

    # Combine the collected parts into an email string
    email_address = "".join(email_parts).replace(" ", "")  # Ensure no spaces

    # Validate and append domain if missing
    if "@" not in email_address:
        email_address += "@gmail.com"
    elif "." not in email_address.split("@")[-1]:
        email_address += ".com"

    print(f"Final email address: '{email_address}'")  # Debugging

    # Check if email is valid
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_address):
        speak(f"The email address {email_address} seems invalid. Please try again.")
        return spell_email()

    speak(f"Email address captured as {email_address}")
    return email_address

def sendEmail(to, content):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login('veturisathvik04@gmail.com', 'oacmdnrhuyqrgogq')
        server.sendmail('veturisathvik04@gmail.com', to, content)
        server.close()
        speak("Email has been sent successfully!")
    except socket.gaierror:
        speak("Network error. Please check your internet connection.")
    except smtplib.SMTPAuthenticationError:
        speak("Authentication failed. Check your email credentials.")
    except Exception as e:
        speak("Unable to send the email due to an error.")
        print(e)

def play_on_youtube(song):
    try:
        pywhatkit.playonyt(song)
    except requests.exceptions.SSLError:
        speak(f"Playing {song} on YouTube")
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")

def save_user_action(action_vector):
    # Find the corresponding action label from the reverse action map
    action_label = reverse_action_map.get(tuple(action_vector[:10]), "unknown action")

    # Write action vector + action label to the CSV file
    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(action_vector + [action_label])

# Function to load user actions from CSV file
def load_user_actions():
    actions = []
    labels = []
    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 11:
                    continue  # Skip malformed rows
                try:
                    # Parse the first 6 elements as integers (the action vector)
                    action = list(map(int, row[:10]))
                    # The 7th element is the action label (string)
                    label = row[10]
                    actions.append(action)
                    labels.append(label)
                except ValueError as e:
                    print(f"Skipping invalid row: {row} - Error: {e}")
    except FileNotFoundError:
        pass  # Return empty if the file does not exist yet
    return actions, labels

recent_recommendations = []
def recommend_next_action(current_action):
    global recent_recommendations  # Track recent recommendations
    action_vector = action_map.get(current_action, [0] * 10)
    actions, labels = load_user_actions()

    if not actions:
        speak("I don't have enough data to recommend anything yet.")
        return "no recommendation"

    # Initialize KNN with a small number of neighbors
    knn = KNeighborsClassifier(n_neighbors=min(5, len(actions)))
    knn.fit(actions, labels)

    # Get the nearest neighbors for the current action
    distances, indices = knn.kneighbors([action_vector])

    # Iterate over the nearest neighbors to find a diverse suggestion
    for idx in indices[0]:
        suggested_action = labels[idx]
        if (suggested_action != current_action and
                suggested_action not in recent_recommendations):
            # Store the suggestion in recent_recommendations
            recent_recommendations.append(suggested_action)

            # Keep only the last 5 recommendations for diversity
            if len(recent_recommendations) > 5:
                recent_recommendations.pop(0)

            return suggested_action

    # Fallback if no new recommendation is found
    return "no recommendation"


def verifyPassword():
    speak("Please speak your password to continue")
    user_password = takeCommand().lower()  # Convert user voice input to lower case for comparison
    if user_password == password:
        speak("Password matched. You may proceed.")
        return True
    else:
        speak("Password did not match. You are not authorized.")
        return False
# List of pre-selected email addresses
email_list = ["veturisathvik@gmail.com", "veturisathvik10@gmail.com","21ve1a6629@sreyas.ac.in"]

# Function to schedule the meeting for tomorrow
def scheduleMeeting():
    try:
        # Get the current date and calculate tomorrow's date
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        subject = f"Scheduled Meeting for {tomorrow.strftime('%A, %B %d, %Y')}"
        body = f"This is a reminder for the meeting scheduled for {tomorrow.strftime('%A, %B %d, %Y')} at 10:00 AM."
        content = f"Subject: {subject}\n\n{body}"
        for email in email_list:
            sendEmail(email, content)
        speak(f"Meeting scheduled for {tomorrow.strftime('%A, %B %d, %Y')} successfully and emails sent!")
    except Exception as e:
        print(e)
        speak("Sorry, I am unable to schedule the meeting.")
if __name__ == "__main__":
    wishMe()
    while True:
        query = takeCommand().lower()
        if 'wikipedia' in query:
            speak('Searching Wikipedia...')
            results = wikipedia.summary(query.replace("wikipedia", ""), sentences=4)
            speak("According to Wikipedia")
            print(results)
            speak(results)
            save_user_action(action_map['search wikipedia'] + [2])
        
        elif 'open youtube' in query:
            webbrowser.open("youtube.com")
            save_user_action(action_map['open youtube'] + [0])
        elif 'open google' in query:
            webbrowser.open("google.com")
            save_user_action(action_map['open google'] + [3])
        
        elif 'play' in query and 'on youtube' in query:
            song = query.replace('play', '').replace('on youtube', '')
            play_on_youtube(song)
            save_user_action(action_map['play song on youtube'] + [1])
        
        elif 'open vs code' in query:
            codePath = r"C:\path\to\VSCode\Code.exe"
            os.startfile(codePath)
            save_user_action(action_map['open vs code'] + [4])
        elif 'the time' in query:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")  
            speak(f"Sir, the time is {strTime}")
        elif 'send email' in query:
            if verifyPassword():
                speak("What should I say?")
                content = takeCommand()
                recipient = spell_email()
                if recipient:
                    speak(f"Sending email to {recipient}")
                    sendEmail(recipient, content)
                    save_user_action(action_map['send email'] + [5])
                else:
                    speak("Invalid email address.")
            else:
                 speak("Email sending operation aborted due to incorrect password.")
        elif 'schedule a meeting' in query:
            speak("You are trying to open the email and schedule a meeting. Password verification required.")
    
            if verifyPassword():  # Verify password before proceeding
              speak("Opening your email and scheduling a meeting for tomorrow.")
              webbrowser.open("https://mail.google.com")
              scheduleMeeting()
              save_user_action(action_map['schedule meeting'] + [7])
            else:
                speak("Operation aborted due to incorrect password.")
        elif 'open stack overflow' in query:
            webbrowser.open("stack overflow.com")
            save_user_action(action_map['open stackoverflow'] + [6])
        elif 'open email' in query:
            speak("You are trying to open the email. Password verification required.")
            save_user_action(action_map['open email'] + [8])
            if verifyPassword():  # Verify password before opening the email
               speak("Opening your email")
               webbrowser.open("https://mail.google.com")
            else:
                speak("Email opening operation aborted due to incorrect password.")

        elif 'power off' in query:
            speak("See you soon friend")
            os.system("shutdown /s /t 1")
            save_user_action(action_map['power off'] + [9])
        next_action = recommend_next_action(query)
        if next_action != "no recommendation":
            speak(f"Based on your previous actions, you may want to {next_action}")
