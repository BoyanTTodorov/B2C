Install the required packages:

bash
Copy code
pip install pyodbc ttkbootstrap
Ensure you have the required ODBC drivers installed for your database.

Usage
Run the application:

bash
Copy code
python main.py
Login:

Enter your username and password in the login window.
Interact with the application:

The main window provides a tabbed interface for different queries such as Receiving, Errors, Sorting, Shipping, and Labels.
Use the provided buttons and checkboxes to perform actions on the displayed data.
Features
User Authentication:

Login system to secure access to the application.
Database Interaction:

Execute queries and display results in a tabbed interface.
Support for multiple tables and customizable queries.
Custom Message Boxes:

Informational and error message boxes for user feedback.
File Structure
app.py:

Defines the main application interface and its components.
custom_messagebox.py:

Contains custom message box classes for displaying information and error messages.
database_manager.py:

Manages the database connection and query execution.
login_window.py:

Defines the login window and handles user authentication.
main.py:

Entry point of the application that initializes and runs the application.
Contributing
Fork the repository.
Create your feature branch: git checkout -b feature/my-new-feature
Commit your changes: git commit -m 'Add some feature'
Push to the branch: git push origin feature/my-new-feature
Submit a pull request.
License
This project is licensed under the MIT License.

Acknowledgments
Inspiration and resources from the Python and Tkinter communities.