import re
import datetime
import tkinter as tk
from app.features.weather import handle_weather_query
from app.features.ai import get_ai_response
from app.features.image_generate import generate_image
from app.features.file_analyzer import query_uploaded_files
from app.features.greetme import greetMe
import webbrowser
import os
from langdetect import detect
from deep_translator import GoogleTranslator
from app.features.google_search import handle_google_search
from app.features.website import handle_open_website, handle_close_website

class AIAgent:
    def __init__(self, app):
        self.app = app
        self.intent_routes = {
            "greet": {
                "keywords": ["greetings"],
                "handler": self.handle_greet,
            },
            "get_time": {
                "keywords": ["time"],
                "handler": self.handle_get_time,
            },
            "reset_chat": {
                "keywords": ["reset chat", "clear chat"],
                "handler": self.handle_reset_chat,
            },
            "stop_speech": {
                "keywords": ["stop talking", "be quiet", "stop speech"],
                "handler": self.handle_stop_speech,
            },
            "weather": {
                "keywords": ["weather", "forecast", "temperature"],
                "handler": self.handle_weather,
            },
            "generate_image": {
                "keywords": ["generate image", "create image", "draw"],
                "handler": self.handle_image_generation,
            },
            "open_website": {
                "keywords": ["open", "launch", "go to"],
                "handler": handle_open_website,
            },
            "close_website": {
                "keywords": ["close browser", "close website"],
                "handler": handle_close_website,
            },
            "file_query": {
                "keywords": ["analyze file", "what does the file say", "summarize the document"],
                "handler": self.handle_file_query,
            },
            "google_search": {
                "keywords": ["google search", "search google for", "google"],
                "handler": handle_google_search,
            },
        }
        self.ai_brain_context = self.load_ai_brain()

    def load_ai_brain(self):
        try:
            with open("ai_brain.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            print("[Warning] ai_brain.md not found.")
            return "You are a helpful AI assistant named Jenny."

    def process_query(self, query):
        # 1. Translate query to English
        try:
            lang = detect(query)
            if lang != "en":
                query = GoogleTranslator(source='auto', target='en').translate(query)
        except Exception as e:
            print(f"[Translation Error] {e}")
            # Proceed with the original query if translation fails
            pass

        # 2. Detect intent
        intent = self.detect_intent(query)

        # 3. If an intent is detected, execute the handler and return its response
        if intent and intent in self.intent_routes:
            handler = self.intent_routes[intent]["handler"]
            response = handler(query) # The handler will perform the action and return the response
            return response
        else:
            # 4. If no intent is detected, treat as a general query
            ai_response = get_ai_response(query, self.app.message_history, self.ai_brain_context)
            return ai_response

    def detect_intent(self, query):
        query_lower = query.lower()
        for intent, data in self.intent_routes.items():
            for keyword in data["keywords"]:
                if keyword in query_lower:
                    return intent
        return None

    def handle_greet(self, query):
        return greetMe()

    def handle_get_time(self, query):
        time_str = f"The time is {datetime.datetime.now().strftime('%H:%M:%S')}"
        return time_str

    def handle_reset_chat(self, query):
        self.app.chat_area.config(state="normal")
        self.app.chat_area.delete("1.0", tk.END)
        self.app.chat_area.config(state="disabled")
        self.app.message_history = []
        return "Chat has been reset."

    def handle_stop_speech(self, query):
        self.app.stop_speech()
        return "Speech stopped."

    def handle_weather(self, query):
        weather_response = handle_weather_query(query)
        return weather_response

    def handle_image_generation(self, query):
        return self.app.handle_image_generation(query)

    def handle_file_query(self, query):
        file_query_response = query_uploaded_files(query)
        return file_query_response