
# B2C Project

##Inbound

## Project Overview
This project is a Python application with several key components, each responsible for different functionalities. The main aspects include user authentication, database operations, a graphical user interface (GUI), and background scanning tasks. There are three folders representing different parts of the return flow: Inbound, Quality Check, and Admin. Note that the admin part of the programs and connection credentials are not included.

## Installation
To set up the project, you need to install the necessary dependencies listed in the `requirements.txt` file. This can be done using the following command:

```bash
pip install -r requirements.txt
```

The dependencies include:

- `ttkbootstrap`: A library to enhance the look and feel of Tkinter applications.
- `keyboard`: Used for capturing keyboard events.
- `pyodbc`: A Python library to connect to ODBC databases.
- `requests`: A library for making HTTP requests.
- `pillow`: A library for image processing.

## Usage
To run the application, start by executing the `main.py` file:

```bash
python main.py
```

## Components

### Login (`login.py`)
- Handles user authentication.
- Ensure user credentials are set up correctly to allow access to the application.

### Database Operations (`database.py`)
- Manages connections and operations with the database.
- Important to verify database connection settings to ensure smooth operation.

### Main Application (`main.py`)
- Acts as the main entry point of the application.
- Orchestrates the initialization and execution of the different components.

### User Interface (`UI.py`)
- Contains code for the graphical user interface.
- Likely uses `ttkbootstrap` to enhance the appearance of the UI.

### Scanner Worker (`scanner_worker.py`)
- Manages background tasks related to scanning.
- Ensures that scanning operations do not block the main application thread.

### `.gitignore`
- Specifies files and directories to be ignored by Git, typically to prevent sensitive or unnecessary files from being committed to the repository.

### `LICENSE`
- Contains the license information for the project, detailing the terms under which the project can be used and distributed.

## File Descriptions

### `database.py`
- Responsible for database-related operations.
- Likely includes functions for connecting to the database, executing queries, and handling data transactions.

### `login.py`
- Handles user authentication, including verifying credentials and managing login sessions.

### `main.py`
- Serves as the starting point for the application.
- Initializes the necessary components and starts the application.

### `requirements.txt`
- Lists all the dependencies required to run the project, which need to be installed before running the application.

### `scanner_worker.py`
- Manages scanning tasks that need to run in the background, allowing the main application to remain responsive.

### `UI.py`
- Contains the code for building and managing the user interface of the application, likely using Tkinter and `ttkbootstrap` for a modern look.

## License
The project is licensed under a specific license mentioned in the `LICENSE` file, which outlines the permissions and limitations for using and distributing the project.

## Contributing
Contributions to the project are welcome. Contributors are encouraged to read the contributing guidelines (typically found in a `CONTRIBUTING.md` file) for details on submitting pull requests.

## Admin Panel

### Overview
The application is a Tkinter-based GUI application that interfaces with a database. It includes functionalities for user login, displaying various operations (such as Receiving, Errors, Sorting, Shipping, and Labels), and handling user interactions through a graphical interface.

### File Descriptions

#### `app.py`
- Defines the `App` class, which is a `ttk.Frame` based GUI application.
- Sets up the main user interface, including various tabs and widgets.
- The `setup_ui` method configures the UI elements and their layout.
- The class interacts with a database through the `DatabaseManager` and displays custom messages using `CustomMessageBox`.

#### `custom_messagebox.py`
- Contains the `CustomMessageBox` class.
- Provides static methods to show different types of message boxes (`show_info` and `show_error`) using Tkinter's messagebox.

#### `database_manager.py`
- Defines the `DatabaseManager` class responsible for database connections and operations.
- Uses `pyodbc` for connecting to a database.
- Includes methods to connect to the database and execute queries.
- Database credentials are fetched from `user_credential`.

#### `login_window.py`
- Defines the `LoginWindow` class, which is a `tk.Toplevel` window for user login.
- The UI includes fields for username and password, and it verifies credentials using the `DatabaseManager`.
- Upon successful login, it initializes the main application window.

#### `main.py`
- The entry point of the application.
- Initializes the main Tkinter root window and sets up the application style using `ttkbootstrap`.
- Creates instances of `DatabaseManager`, `App`, and `LoginWindow`.
- The main window is hidden initially and shown only after a successful login.

### Functionality Workflow

#### Application Startup (`main.py`)
- The application starts by running `main.py`, which sets up the Tkinter root window and initializes the `DatabaseManager`.
- A theme is applied using `ttkbootstrap.Style`.

#### User Login (`login_window.py`)
- The `LoginWindow` is displayed, prompting the user to enter their username and password.
- Credentials are validated against the database using methods provided by `DatabaseManager`.
- On successful login, the main application window (`App`) is shown.

#### Main Application Interface (`app.py`)
- The `App` class sets up the main interface with tabs for various operations.
- Each tab contains widgets such as buttons and checkboxes for performing specific actions.
- The application interacts with the database to fetch and display relevant data.

#### Custom Message Boxes (`custom_messagebox.py`)
- Throughout the application, `CustomMessageBox` is used to display information or error messages to the user.

### Summary
The application is a structured Tkinter-based GUI that provides a tabbed interface for interacting with a database. It includes user authentication and various operations organized into tabs. The application is modular, with separate files handling different aspects of functionality such as database management, user interface, and custom message handling.
