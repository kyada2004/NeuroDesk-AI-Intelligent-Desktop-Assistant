import customtkinter as ctk
from tkinter import messagebox
from app.core.utils import db_connect


import os

def show_login_window(parent=None, on_success=None, icon_path=None):
    # Create popup
    login_frame = ctk.CTkToplevel(parent)
    login_frame.title("Login")
    login_frame.geometry("400x280")
    login_frame.resizable(False, False)

    if icon_path and os.path.exists(icon_path):
        login_frame.iconbitmap(icon_path)

    # Center the window
    login_frame.update_idletasks()
    w, h = 400, 280
    x = (login_frame.winfo_screenwidth() // 2) - (w // 2)
    y = (login_frame.winfo_screenheight() // 2) - (h // 2)
    login_frame.geometry(f"{w}x{h}+{x}+{y}")

    # gmail field
    ctk.CTkLabel(login_frame, text="gmail:").pack(pady=(20, 5))
    gmail_entry = ctk.CTkEntry(login_frame, width=280)
    gmail_entry.pack()

    # Password field
    ctk.CTkLabel(login_frame, text="Password:").pack(pady=(10, 5))
    password_entry = ctk.CTkEntry(login_frame, show="*", width=280)
    password_entry.pack()

    def login_action():
        gmail = gmail_entry.get().strip()
        password = password_entry.get().strip()

        if not gmail or not password:
            messagebox.showwarning("Input Required", "Please enter gmail and password")
            return

        try:
            conn = db_connect()
            cur = conn.cursor()
            # ✅ Note: check if your DB column is 'first_name' or 'first_name'
            cur.execute(
                "SELECT first_name, last_name FROM users WHERE gmail=? AND password=?",
                (gmail, password),
            )
            row = cur.fetchone()

            if row:
                login_frame.destroy()
                if on_success:
                    on_success(row[0], row[1], gmail)  # callback to ChatApplication.login_user
            else:
                messagebox.showerror("Login Failed", "Invalid credentials")

        except Exception as e:
            messagebox.showerror("Error", f"Database error:\n{e}")
        finally:
            conn.close()

    # Login button
    ctk.CTkButton(login_frame, text="Login", width=120, command=login_action).pack(pady=25)
