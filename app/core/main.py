import customtkinter as ctk
from tkinter import scrolledtext, messagebox, filedialog, Toplevel, Label, filedialog
import tkinter as tk
import speech_recognition as sr
import datetime
import threading
import webbrowser
import queue
import re
import os
import json
import requests
from g4f.client import Client
from PIL import Image, ImageTk
import io
from app.features.file_analyzer import store_uploaded_file , query_uploaded_files
from app.auth.login import show_login_window
from app.auth.register import show_register_window
from app.core.utils import say, db_connect, init_db
from app.features.greetme import greetMe
from app.features.weather import handle_weather_query
from app.features.ai import get_ai_response
from app.features.image_generate import generate_image
from langdetect import detect
from deep_translator import GoogleTranslator
from gtts import gTTS
from playsound import playsound
import tempfile
from app.core.agent import AIAgent


speech_queue = queue.Queue()
SESSION_FILE = "session.json"


def speech_worker():
    while True:
        text = speech_queue.get()
        if text is None:
            break
        say(text)


threading.Thread(target=speech_worker, daemon=True).start()


class ChatApplication(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jenny AI Chatbot")
        self.geometry("900x650")
        self.minsize(800, 600)

        self.icon_path = os.path.join("app", "static", "ai.ico")
        self.current_user = None
        self.session_id = None
        self.dropdown_menu = None
        self.history_sidebar = None
        self.guest_question_count = 0
        self.max_guest_questions = 10
        self.image_generation_count = 0
        self.image_limit_logged_in = 5
        self.image_limit_guest = 2
        self.message_history = []
        
        self.agent = AIAgent(self)

        self.setup_ui()
        init_db()
        self.auto_login()
        greetMe()

    def setup_ui(self):
        if os.path.exists(self.icon_path):
            self.iconbitmap(self.icon_path)

        self.setup_navbar()
        self.setup_sidebar()
        self.setup_main_frame()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def auto_login(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    data = json.load(f)
                exp = datetime.datetime.strptime(data["expires_at"], "%Y-%m-%d")
                if datetime.datetime.now() <= exp:
                    self.login_user(
                        data["first_name"], data["last_name"], data["gmail"]
                    )
            except Exception as e:
                print(f"[AutoLogin Error] {e}")

    def save_session(self):
        if self.current_user:
            expire_date = (
                datetime.datetime.now() + datetime.timedelta(days=30)
            ).strftime("%Y-%m-%d")
            session = {
                "first_name": self.current_user["first_name"],
                "last_name": self.current_user["last_name"],
                "gmail": self.current_user["gmail"],
                "expires_at": expire_date,
            }
            with open(SESSION_FILE, "w") as f:
                json.dump(session, f)

    def clear_session(self):
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

    def setup_navbar(self):
        self.navbar = ctk.CTkFrame(self, height=55, fg_color="#202123")
        self.navbar.pack(fill="x", side="top")

        self.title_label = ctk.CTkLabel(
            self.navbar,
            text="🧐 Jenny AI Chatbot",
            font=("Segoe UI", 20, "bold"),
            text_color="#F0F0F0",
        )
        self.title_label.pack(side="left", padx=20, pady=5)

        self.right_frame = ctk.CTkFrame(self.navbar, fg_color="transparent")
        self.right_frame.pack(side="right", padx=15)

        self.update_navbar_buttons()

    def setup_sidebar(self):
        self.history_sidebar = ctk.CTkScrollableFrame(
            self, width=260, fg_color="#2B2D31", corner_radius=0
        )
        self.history_sidebar.pack(side="left", fill="y")
        self.history_sidebar.pack_forget()

    def setup_main_frame(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#343541")
        self.main_frame.pack(
            padx=10, pady=(10, 0), fill="both", expand=True, side="left"
        )

        self.chat_display_frame = ctk.CTkFrame(self.main_frame, fg_color="#343541")
        self.chat_display_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        self.chat_area = scrolledtext.ScrolledText(
            self.chat_display_frame,
            font=("Segoe UI", 13),
            wrap=tk.WORD,
            bd=0,
            bg="#1E1E20",
            fg="#EDEDED",
            insertbackground="#EDEDED",
        )
        self.chat_area.pack(fill="both", expand=True)
        self.chat_area.config(state="disabled")

        self.thinking_label = ctk.CTkLabel(self.main_frame, text="Jenny is thinking...", font=("Segoe UI", 12, "italic"))

        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="#202123")
        self.bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.input_entry = ctk.CTkEntry(
            self.bottom_frame,
            height=48,
            font=("Segoe UI", 14),
            placeholder_text="Message Jenny...",
            text_color="white",
            fg_color="#343541",
            border_color="#3a3a3a",
            corner_radius=15,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self.process_command())

        ctk.CTkButton(
            self.bottom_frame,
            text="📁 Upload",
            width=80,
            height=48,
            command=self.upload_file,
            font=("Segoe UI", 14),
            corner_radius=15,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            self.bottom_frame,
            text="🎤",
            width=45,
            height=48,
            command=self.voice_command,
            font=("Segoe UI", 16),
            corner_radius=15,
        ).pack(side="left")
        ctk.CTkButton(
            self.bottom_frame,
            text="Send",
            width=80,
            height=48,
            command=self.process_command,
            font=("Segoe UI", 14),
            corner_radius=15,
        ).pack(side="left", padx=(10, 0))

        speech_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        speech_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.speech_enabled = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            speech_frame,
            text="🔊 Enable Speech",
            variable=self.speech_enabled,
            font=("Segoe UI", 12),
        ).pack(anchor="w")

    def upload_file(self):
        file_paths = filedialog.askopenfilenames(title="Select file(s)")
        if file_paths:
            self.chat_area.config(state="normal")
            for file_path in file_paths:
                result = store_uploaded_file(file_path)
                self.chat_area.insert(tk.END, f"{result}\n\n")
            self.chat_area.config(state="disabled")
            self.chat_area.yview_moveto(1)

    def handle_query(self, query):
        result = query_uploaded_files(query)
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"🤖 {result}\n\n")
        self.chat_area.config(state="disabled")
        self.chat_area.yview_moveto(1)
        

    def update_navbar_buttons(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        if self.current_user:
            initials = (
                self.current_user["first_name"][:1] + self.current_user["last_name"][:1]
            ).upper()
            profile_btn = ctk.CTkButton(
                self.right_frame,
                text=f"👤 {initials}",
                width=50,
                command=self.toggle_profile_dropdown,
                corner_radius=30,
                font=("Segoe UI", 14),
            )
            profile_btn.pack(side="left", padx=5)

            self.dropdown_menu = tk.Menu(self, tearoff=0)
            self.dropdown_menu.add_command(
                label="History", command=self.toggle_history_sidebar
            )
            self.dropdown_menu.add_command(label="Logout", command=self.logout_user)
        else:
            ctk.CTkButton(
                self.right_frame, text="Register", width=70, command=self.show_register
            ).pack(side="left", padx=5)
            ctk.CTkButton(
                self.right_frame, text="Login", width=70, command=self.show_login
            ).pack(side="left", padx=5)

    def toggle_profile_dropdown(self):
        try:
            x = self.right_frame.winfo_rootx()
            y = self.right_frame.winfo_rooty() + self.right_frame.winfo_height()
            self.dropdown_menu.tk_popup(x, y)
        finally:
            self.dropdown_menu.grab_release()

    def save_query_response(self, user_gmail, session_id, question, answer):
        try:
            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO responses (user_gmail, session_id, question, answer, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (user_gmail, session_id, question, answer),
            )
            conn.commit()
        except Exception as e:
            print(f"[DB Save Error] {e}")
        finally:
            conn.close()
            
    def center_window(window, width, height):
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def show_login(self):
        show_login_window(parent=self, on_success=self.login_user, icon_path=self.icon_path)

    def show_register(self):
        show_register_window(parent=self, on_success=self.login_user, icon_path=self.icon_path)

    def login_user(self, first_name, last_name, gmail):
        self.current_user = {
            "first_name": first_name,
            "last_name": last_name,
            "gmail": gmail,
        }
        self.session_id = datetime.datetime.now().strftime("%Y-%m-%d")
        self.update_navbar_buttons()
        self.respond(f"Welcome back, {first_name}!")
        self.save_session()

    def logout_user(self):
        self.current_user = None
        self.session_id = None
        self.update_navbar_buttons()
        self.history_sidebar.pack_forget()
        self.clear_session()
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state="disabled")
        self.message_history = []
        self.respond("You have been logged out.")

    def handle_image_generation(self, query):
        limit = self.image_limit_logged_in if self.current_user else self.image_limit_guest
        if self.image_generation_count >= limit:
            return "⚠️ You have reached the image generation limit. Please login or wait."

        match = re.search(r"(generate|create) image(?: of| for| with)? (.+)", query.lower())
        prompt = match.group(2) if match else query.replace("generate image", "").replace("create image", "").strip()

        if not prompt:
            return "Please specify what you want to generate."

        image_url = generate_image(prompt)

        try:
            image_data = requests.get(image_url).content
            image_pil_preview = Image.open(io.BytesIO(image_data)).resize((256, 256))
            image_tk_preview = ImageTk.PhotoImage(image_pil_preview)

            self.chat_area.config(state="normal")
            image_label = tk.Label(self.chat_area, image=image_tk_preview, cursor="hand2", bg="#9C9C9C")
            image_label.image = image_tk_preview
            image_label.pack_propagate(False)
            image_label.bind("<Button-1>", lambda e: self.open_zoom_window(image_data))
            self.chat_area.window_create(tk.END, window=image_label)
            self.chat_area.insert(tk.END, "\n\n")
            self.chat_area.config(state="disabled")
            self.chat_area.yview_moveto(1)

            if not hasattr(self, 'image_refs'):
                self.image_refs = []
            self.image_refs.append(image_tk_preview)

            self.image_generation_count += 1
            if self.speech_enabled.get():
                speech_queue.put("Image generated successfully.")
            
            return image_url

        except Exception as e:
            print(f"[Image Display Error] {e}")
            return "❌ Failed to display image."

    def open_zoom_window(self, image_data):
        try:
            zoom_win = Toplevel(self)
            zoom_win.title("Zoomed Image")
            zoom_win.geometry("600x600")
            if os.path.exists(self.icon_path):
                zoom_win.iconbitmap(self.icon_path)

            image_pil = Image.open(io.BytesIO(image_data))
            image_tk = ImageTk.PhotoImage(image_pil)

            img_label = tk.Label(zoom_win, image=image_tk)
            img_label.image = image_tk
            img_label.pack(padx=10, pady=10, expand=True)

            def download_image():
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[
                        ("PNG files", "*.png"),
                        ("JPEG files", "*.jpg"),
                        ("All files", "*.*"),
                    ],
                )
                if file_path:
                    try:
                        image_pil.save(file_path)
                        messagebox.showinfo("Saved", f"Image saved to:\n{file_path}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not save image: {e}")

            download_btn = ctk.CTkButton(
                zoom_win, text="⬇️ Download Image", command=download_image
            )
            download_btn.pack(pady=(5, 15))

        except Exception as e:
            messagebox.showerror("Error", f"Zoom view failed: {e}")

    def toggle_history_sidebar(self):
        if self.history_sidebar.winfo_ismapped():
            self.history_sidebar.pack_forget()
        else:
            self.populate_history_sidebar()
            self.history_sidebar.pack(side="left", fill="y")

    def populate_history_sidebar(self):
        for widget in self.history_sidebar.winfo_children():
            widget.destroy()

        if not self.current_user or not self.current_user.get("gmail"):
            ctk.CTkLabel(self.history_sidebar, text="Login to view history").pack(pady=10)
            return

        try:
            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT session_id FROM responses
                WHERE user_gmail = ?
                ORDER BY session_id DESC
                LIMIT 30
            """, (self.current_user['gmail'],))
            sessions = cursor.fetchall()

            if not sessions:
                ctk.CTkLabel(self.history_sidebar, text="No history found.").pack(pady=10)
                return

            ctk.CTkLabel(self.history_sidebar, text=f"📜 History for {self.current_user['first_name']}", font=("Segoe UI", 13, "bold")).pack(pady=8)

            for session in sessions:
                session_id = session[0]
                btn = ctk.CTkButton(self.history_sidebar, text=session_id, command=lambda s=session_id: self.load_chat_history(s))
                btn.pack(pady=2, padx=5, fill="x")

        except Exception as e:
            print("[History Error]", e)
        finally:
            if conn:
                conn.close()

    def load_chat_history(self, session_id):
        try:
            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT question, answer FROM responses
                WHERE user_gmail = ? AND session_id = ?
                ORDER BY created_at ASC
            """, (self.current_user['gmail'], session_id))
            rows = cursor.fetchall()

            self.chat_area.config(state="normal")
            self.chat_area.delete("1.0", tk.END)
            self.message_history = []

            for q, a in rows:
                self.chat_area.insert(tk.END, f"You: {q}\n")
                self.message_history.append({"role": "user", "content": q})
                self.chat_area.insert(tk.END, f"Jenny: {a}\n\n")
                self.message_history.append({"role": "assistant", "content": a})
            
            self.chat_area.config(state="disabled")
            self.chat_area.yview_moveto(1)
            
            self.session_id = session_id

        except Exception as e:
            print(f"[Load History Error] {e}")
        finally:
            if conn:
                conn.close()

    def process_command(self, query=None):
        query = query or self.input_entry.get().strip()
        if not query:
            return

        # Create a new session if the day has changed
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if self.session_id != current_date:
            self.session_id = current_date
            self.chat_area.config(state="normal")
            self.chat_area.delete("1.0", tk.END)
            self.chat_area.config(state="disabled")
            self.message_history = []

        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"You: {query}\n")
        self.chat_area.config(state="disabled")
        self.message_history.append({"role": "user", "content": query})
        self.input_entry.delete(0, tk.END)

        self.thinking_label.pack(pady=5)
        threading.Thread(target=self._process_query_thread, args=(query,)).start()

    def _process_query_thread(self, query):
        answer = self.agent.process_query(query)
        self.after(0, self._update_chat_with_response, answer, query)

    def _update_chat_with_response(self, answer, query):
        self.thinking_label.pack_forget()
        if answer:
            self.respond(answer)
        else:
            answer = "I'm sorry, I don't understand that. Can you please rephrase?"
            self.respond(answer)

        if self.current_user:
            self.save_query_response(self.current_user["gmail"], self.session_id, query, answer)
            if self.history_sidebar.winfo_ismapped():
                self.populate_history_sidebar()
        else:
            self.guest_question_count += 1
            if self.guest_question_count >= self.max_guest_questions:
                self.respond(
                    "⚠️ You've reached the free limit. Please log in to continue."
                )
                self.after(1000, self.show_login)

    def respond(self, message):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"Jenny: {message}\n\n")
        self.chat_area.config(state="disabled")
        self.chat_area.yview_moveto(1)
        self.message_history.append({"role": "assistant", "content": message})
        if self.speech_enabled.get():
            speech_queue.put(message)

    def voice_command(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.respond("Listening...")
            try:
                audio = recognizer.listen(source, timeout=5)
                query = recognizer.recognize_google(audio)

                detected_lang = detect(query)
                print(f"[Detected Language] {detected_lang} | Query: {query}")

                if detected_lang != "en":
                    translated_query = GoogleTranslator(
                        source="auto", target="en"
                    ).translate(query)
                else:
                    translated_query = query

                self.chat_area.config(state="normal")
                self.chat_area.insert(tk.END, f"You (Voice): {query}\n")
                self.chat_area.config(state="disabled")

                self.process_command(translated_query)

            except sr.UnknownValueError:
                self.respond("Sorry, I didn't catch that.")
            except sr.RequestError:
                self.respond("Voice recognition error.")
            except Exception as e:
                self.respond("Something went wrong.")
                print(f"[Voice Error] {e}")

    def speak_text(self, text, lang_code="en"):
        try:
            tts = gTTS(text=text, lang=lang_code)
            with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
                tts.save(fp.name)
                playsound(fp.name)
        except Exception as e:
            print(f"[TTS Error] {e}")

    def stop_speech(self):
        while not speech_queue.empty():
            try:
                speech_queue.get(block=False)
            except queue.Empty:
                continue

    def on_exit(self):
        speech_queue.put(None)
        self.destroy()