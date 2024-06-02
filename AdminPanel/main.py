import tkinter as tk
from ttkbootstrap import Style
from database_manager import DatabaseManager
from app import App
from login_window import LoginWindow

if __name__ == "__main__":
    db_manager = DatabaseManager()
    root = tk.Tk()
    root.withdraw()  # Hide the main window until login is successful
    style = Style(theme='superhero')  # Set a theme for nicer widgets
    app = App(root, db_manager)
    login_window = LoginWindow(root, db_manager)
    root.mainloop()
