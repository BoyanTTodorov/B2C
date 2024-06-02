import tkinter as tk
from tkinter import messagebox
from UI import UI
import ttkbootstrap as ttk
import re
import os
# icon_path = os.path.abspath('logo.ico')
def sanitize_input(input_str):
    # Remove leading and trailing whitespace
    input_str = input_str.strip()
    # Define a regular expression pattern to allow only alphanumeric characters and underscore
    pattern = r'[^a-zA-Z0-9_]'
    # Use the regular expression to remove any characters that don't match the pattern
    sanitized_input = re.sub(pattern, '', input_str)
    return sanitized_input

def start_login_window():
    window = tk.Tk()
    window.geometry('300x180')
    window.title('Login')
    # window.iconbitmap(icon_path)
    def login():
        # Get the username input and sanitize it
        username = sanitize_input(inp_username.get())

        # Check if the sanitized username is empty
        if not username:
            messagebox.showerror("Login Failed", "Username cannot be empty.")
            return

        # Attempt to log in with the sanitized username
        try:
            # Perform login logic here
            # For demonstration purposes, assume successful login
            window.destroy()
            app = UI(username)
            app.run()
        except Exception as e:
            messagebox.showerror("Login Failed", f"An error occurred during login: {str(e)}")

    lbl_username = ttk.Label(window, text='Reflex Username:')
    lbl_username.pack(pady=(20, 10))
    inp_username = ttk.Entry(window)
    inp_username.pack()

    btn_login = ttk.Button(window, text='Login', command=login)
    btn_login.pack(pady=20)

    window.mainloop()

# # Start the login window
# start_login_window()
