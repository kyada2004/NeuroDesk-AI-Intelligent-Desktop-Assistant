# app/auth/register.py
import customtkinter as ctk
from tkinter import messagebox
from app.core.utils import db_connect


import os

def show_register_window(parent=None, on_success=None, icon_path=None):
    register_frame = ctk.CTkToplevel(parent)
    register_frame.title("Register")
    register_frame.geometry("400x400")
    register_frame.resizable(False, False)

    if icon_path and os.path.exists(icon_path):
        register_frame.iconbitmap(icon_path)

    # Center the window
    register_frame.update_idletasks()
    w, h = 400, 400
    x = (register_frame.winfo_screenwidth() // 2) - (w // 2)
    y = (register_frame.winfo_screenheight() // 2) - (h // 2)
    register_frame.geometry(f"{w}x{h}+{x}+{y}")

    # First Name
    ctk.CTkLabel(register_frame, text="First Name:").pack(pady=(20, 5))
    first_name_entry = ctk.CTkEntry(register_frame, width=280)
    first_name_entry.pack()

    # Last Name
    ctk.CTkLabel(register_frame, text="Last Name:").pack(pady=(10, 5))
    last_name_entry = ctk.CTkEntry(register_frame, width=280)
    last_name_entry.pack()

    # gmail
    ctk.CTkLabel(register_frame, text="gmail:").pack(pady=(10, 5))
    gmail_entry = ctk.CTkEntry(register_frame, width=280)
    gmail_entry.pack()

    # Password
    ctk.CTkLabel(register_frame, text="Password:").pack(pady=(10, 5))
    password_entry = ctk.CTkEntry(register_frame, show="*", width=280)
    password_entry.pack()

    def register_action():
        first = first_name_entry.get().strip()
        last = last_name_entry.get().strip()
        gmail = gmail_entry.get().strip()
        pwd = password_entry.get().strip()

        if not (first and last and gmail and pwd):
            messagebox.showwarning("Input Required", "All fields are required")
            return

        try:
            conn = db_connect()
            cur = conn.cursor()
            # ✅ Match with chatbot DB schema (uses first_name not first_name)
            cur.execute(
                "INSERT INTO users (first_name, last_name, gmail, password) VALUES (?, ?, ?, ?)",
                (first, last, gmail, pwd),
            )
            conn.commit()
            messagebox.showinfo("Success", "Registration successful!")

            register_frame.destroy()
            if on_success:
                on_success(first, last, gmail)  # auto login after register

        except Exception as e:
            if "UNIQUE constraint" in str(e):
                messagebox.showerror("Error", "gmail already exists")
            else:
                messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    # Register button
    ctk.CTkButton(register_frame, text="Register", width=120, command=register_action).pack(pady=25)
