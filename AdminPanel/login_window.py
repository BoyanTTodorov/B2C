import tkinter as tk
from tkinter import ttk
from custom_messagebox import CustomMessageBox

class LoginWindow(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.title("Login")
        self.geometry("300x250")
        self.build_ui()

    def build_ui(self):
        username_label = ttk.Label(self, text="Username:")
        username_label.pack(pady=(20, 5))
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack()

        password_label = ttk.Label(self, text="Password:")
        password_label.pack(pady=(10, 5))
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.pack()

        login_button = ttk.Button(self, text="Login", command=self.check_credentials)
        login_button.pack(pady=20)

    def check_credentials(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username == 'admin' and password == 'admin':
            self.destroy()
            self.parent.deiconify()
        else:
            CustomMessageBox.show_error("Login Failed", "Invalid credentials. Please try again.")
