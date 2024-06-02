import tkinter as tk
from tkinter import ttk
from scanner_worker import ScannerWorker
from datetime import datetime
from database import DatabaseManager
import os
import ttkbootstrap as ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from tkinter import messagebox
# icon_path = os.path.abspath('logo.ico')
class UI(tk.Tk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title('B2C Guess')
        self.geometry('1280x780')  # Increased size of the application
        # self.iconbitmap(icon_path)
        self.scanner_worker = ScannerWorker()
        self.db_manager = DatabaseManager(self.username)
        self.scanned_items = {}  # Dictionary to store scanned items and quantities
        self.create_widgets()
        self.scanning = False
        self.current_image = None
        self.PID = None
        self.SKU = None

    def greet_user(self):
        # Fetch the current user's login name
        username = self.username
        # Format the greeting message to include the username and a prompt to connect the scanner
        greeting_message = f"Welcome to B2C Guess, {username}! Please connect the scanner \n scan PickID after that SKU"
        # Display the formatted greeting message in the text box with a green emoji
        self.update_msg_box(greeting_message, success=True)

    def toggle_scanning(self):
        if not self.scanning:
            if not self.scanner_worker.is_alive():
                self.scanner_worker = ScannerWorker()  # Re-create worker if not alive+
                self.scanner_worker.set_on_scan_callback(self.process_scan)
                self.scanner_worker.start()
                self.start_stop_btn.configure(text='Pause Scanning', bg='orange')  # Change to Pause Scanning in orange
                self.scanning = True
            else:
                self.update_msg_box("Scanner worker is already running.", warning=True)
        else:
            # Check if it is currently paused
            if self.scanner_worker.paused:
                self.scanner_worker.pause()  # Resume scanning
                self.start_stop_btn.configure(text='Pause Scanning', bg='orange')  # Still orange for pausing
                self.update_msg_box("Scanning resumed. 😀", success=True)
            else:
                self.scanner_worker.pause()  # Pause scanning
                self.start_stop_btn.configure(text='Start Scanning', bg='green')  # Change back to Start Scanning in green
                self.update_msg_box("Scanning paused. 😞", warning=True)

    def process_scan(self, scanned_item, code_type):

        if code_type == 'Unknown' or scanned_item is None:
            self.update_msg_box("Incorrect code scanned. Please try again. 😞", warning=True)
            return
        
        elif code_type == 'PID':
            items_and_quantities = self.db_manager.get_pick_id(scanned_item)
            if not items_and_quantities:  # Assuming get_pick_id returns an empty list or None if no data
                self.update_msg_box(f"Unknown PID: {scanned_item}. 😞", warning=True)
                msg = self.db_manager.insert_pick_error_data_pickid(scanned_item,f"Unknown PID: {scanned_item}")
                self.update_msg_box(msg, warning=True)
                return

            self.PID = items_and_quantities[0][0].strip()
            items_and_quantities = self.clean_data(items_and_quantities)
            print(f'PID={self.PID}\n')
            message = f"PID Scanned: {scanned_item}\n"
            self.update_pid_label()
            for pickid, item, qty, modelpartcolor, size in items_and_quantities:
                message += f"PID: {pickid} SKU: {item} Qty: {qty} ModelPartColor: {modelpartcolor} Size: {size}\n"
            self.update_msg_box(message.strip(), success=True)

        elif code_type == 'ORDER66':
                if self.PID is not None:
                    self.db_manager.insert_or_update_label(self.PID)
                    self.update_msg_box(f"{datetime.now().strftime('%H:%M:%S')} Missing label inserted for PID:{self.PID}. 😀", success=True)
                else:
                    self.update_msg_box(f"{datetime.now().strftime('%H:%M:%S')} Please scan PID first. 😞", warning=True)

        elif code_type == 'SKU':
            self.SKU = scanned_item
            self.update_SKU_label()
            self.load_and_display_image(scanned_item)
            pick_id = self.db_manager.check_sku_for_PID(scanned_item, self.PID)
            max_quantity =self.db_manager.get_max_quantity_sku(scanned_item)
            master_data = self.db_manager.check_for_masterdata(scanned_item)
            print(master_data)

            if self.PID is None:
                self.db_manager.insert_pick_error_data_pickid(scanned_item, f"PID{scanned_item} Not Found, Please start with PID. Inserting into error database.")
                self.update_msg_box(f"Scaned {scanned_item}, please start with PICKID.\n 😞", warning=True)
                return
 
            elif master_data is None:
                self.db_manager.insert_error_data(self.PID, scanned_item, f'SKU:{scanned_item} Not Existing in MasterData') #Check current quantity if more max qty reach
                message = f'SKU:{scanned_item} Not Existing in MASTERDATA\n'
                self.update_msg_box(f"{message} 😞", warning=True)
                return
  
            # elif pick_id is None:
            #     self.db_manager.insert_error_data(None, scanned_item, f"There is no PID{scanned_item} Not Found. Inserting into error database.")
            #     self.update_msg_box(f"There is no PID{scanned_item} Not Found. Inserting into error database.\n 😞", warning=True)
            #     return
            
            elif max_quantity is None:
                self.db_manager.insert_error_data(self.PID, scanned_item, f"There is no MAXQT for SKU:{scanned_item}. Inserting into ERRORS database.")
                self.update_msg_box(f"There is no Data received from Guess for SKU:{scanned_item}. Inserting into error database.\n😞", warning=True)
                return

            else:
                currect_PID = self.db_manager.check_sku_for_PID(scanned_item, self.PID)[0][0] or 0

                if str(currect_PID).strip() != str(self.PID).strip() :
                    self.db_manager.insert_error_data(self.PID, scanned_item, f"SKU:{scanned_item} does not match PID:{self.PID}.Please rescan.\nCorrect PID:{currect_PID}")
                    self.update_msg_box(f"SKU:{scanned_item} does not match PID:{self.PID}.Please rescan.\nCorrect PID:{currect_PID}\n 😞", warning=True)
                    return
                else:

                    if master_data is not None and pick_id is not None and (str(currect_PID).strip() != str(self.SKU).strip()):
                        current_qty = self.db_manager.check_receiving_data(currect_PID, scanned_item) or 0
                        max_quantity = self.db_manager.get_max_quantity(scanned_item, currect_PID) or 0

                        print(f"Condition Check -> Current Qty: {current_qty}, Max Qty: {max_quantity}")

                        if max_quantity > current_qty:
                            self.update_msg_box(f'{datetime.now().strftime('%H:%M:%S')} Item Scanned: {scanned_item}\n', success=True)

                            # Getting the Data for new columns
                            new_columns_data = self.db_manager.get_model_link_line_category(scanned_item)
                            modelpart = new_columns_data[1].strip()
                            line = new_columns_data[3].strip()
                            category = new_columns_data[-1].strip()

                            for i in range(len(new_columns_data)):
                                print(new_columns_data[i])

                            if modelpart and line and category:
                                self.db_manager.insert_receiving_data(self.PID, scanned_item.strip(), 1, modelpart, line, category)
                                message = f"SKU Scanned:\n- Code: {scanned_item}\n- Max Quantity: {max_quantity}\n- Current Quantity: {current_qty}\n- Master Data Result: {master_data}\n"
                                self.update_msg_box(message, success=True)
                               
                                self.update_tree_view(scanned_item, str(int(max_quantity) - int(current_qty)) , modelpart, line, category)
                            else:
                                self.update_msg_box(f'{datetime.now().strftime('%H:%M:%S')} Didnt found modelpart Line and Category: {scanned_item}\n Modelpart and Line and Category are not available 😞', warning=True)

                        else:
                            self.update_msg_box(f'{datetime.now().strftime('%H:%M:%S')} Maximum quantity reached for SKU: {scanned_item}\n 😞', warning=True)
                    else:
                        self.update_msg_box("Initial condition failed. 😞", warning=True)
        else:
            # Handle unknown code types with a warning
            self.update_msg_box("Unknown code type scanned. 😞", warning=True)
            

    def load_and_display_image(self, SKU):
        """Fetches the image URL from the database and displays it or a message if no image is available."""
        results = self.db_manager.get_model_link_line_category(SKU)
 
        if results:
            _, _, link, _, _ = results # Extract the image URL
            if link:  # Ensure there's actually a link provided
                self.display_image(link)
            else:
                self.display_message("No image available for this SKU. 😞")
        else:
            self.display_message("No data or image available for this SKU. 😞")

    def display_image(self, image_url):
        """Loads and displays the image from a URL in a separate window, reusing the same window for each new image."""
        try:
            response = requests.get(image_url, verify=False)  # For demonstration; be cautious in production
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            photo = ImageTk.PhotoImage(img)

            if not hasattr(self, 'image_window') or not self.image_window.winfo_exists():
                # Create a new top-level window if it does not exist or has been closed
                self.image_window = tk.Toplevel(self)
                self.image_window.title("Image Display")
                self.image_label = tk.Label(self.image_window)
                self.image_label.pack(fill=tk.BOTH, expand=True)

            # Update the existing window
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Keep a reference

            # Resize window and position next to the main app
            main_x = self.winfo_x()
            main_y = self.winfo_y()
            main_width = self.winfo_width()
            self.image_window.geometry(f"{img.width}x{img.height}+{main_x + main_width + 10}+{main_y}")
        except Exception as e:
            self.display_message("Failed to load image. Error: " + str(e))

    def display_message(self, message):
        """Displays a message in the existing image window or creates a new one if not present."""
        if not hasattr(self, 'image_window') or not self.image_window.winfo_exists():
            self.image_window = tk.Toplevel(self)
            self.image_window.title("Message Display")
            self.image_label = tk.Label(self.image_window, text=message)
            self.image_label.pack(fill=tk.BOTH, expand=True)
        else:
            self.image_label.config(text=message, image='')  # Display the message in the existing label

    def clean_data(self, data):
        if data is None:
            return []
        cleaned_data = []
        for row in data:
            cleaned_row = tuple(item.strip() if isinstance(item, str) else item for item in row)
            cleaned_data.append(cleaned_row)
        return cleaned_data
    
    def clean_and_reconstruct_data(self, data):
        cleaned_data = []
        for row in data[0]:
            # Clean each item in the row by stripping spaces and filtering out 'N/A'
            cleaned_items = [item.strip() for item in row if item.strip() != 'N/A']
            # Append the cleaned items directly if there's only one, or as a list if more
            if len(cleaned_items) == 1:
                cleaned_data.append(cleaned_items[0])  # Append single item directly
            elif cleaned_items:
                cleaned_data.append(cleaned_items)  # Append multiple items as a list
        return cleaned_data

    def update_msg_box(self, text, success=False, warning=False):
        """Updates the message box with the provided text, styling it based on the success or warning flag."""
        # Configure a tag for green text if it's a success message
        if success:
            self.text_box.tag_configure('success', foreground='green', font=('Arial', 12, 'bold'))
            self.text_box.insert(tk.END, f"{text}\n", 'success')
        # Configure a tag for red text if it's a warning message
        elif warning:
            self.text_box.tag_configure('warning', foreground='red', font=('Arial', 12))
            self.text_box.insert(tk.END, f"{text}\n", 'warning')
        else:
            self.text_box.insert(tk.END, f"{text}\n")
        
        # Scroll to the end of the text box after updating, ensuring it's executed in the main GUI thread
        self.text_box.after(100, self.scroll_to_end)

    def scroll_to_end(self):
        self.text_box.see(tk.END)

    def update_tree_view(self, scanned_item, quantity, modelpart, line, category):
        """Updates the tree view with the scanned item information."""
        self.tree_view.insert('', 0, values=(datetime.now().strftime('%H:%M:%S'), scanned_item, quantity, modelpart, line, category))

    def create_widgets(self):
        # Master frame to hold both control and image frames, centrally aligned
        master_frame = tk.Frame(self, padx=10, pady=10)
        master_frame.grid(row=0, column=0, sticky='nsew')

        # Frame for controls with added padding for aesthetics
        control_frame = tk.Frame(master_frame, padx=10, pady=10)
        control_frame.grid(row=0, column=0, sticky='nsew')

        # Frame for the image display with padding
        image_frame = tk.Frame(master_frame, padx=10, pady=10)
        image_frame.grid(row=0, column=1, sticky='nsew')

        # Label for displaying "Current PID"
        self.current_pid_label = tk.Label(control_frame, text="Current PID: ", font=('Arial', 14))
        self.current_pid_label.pack(side=tk.TOP, padx=5, pady=5, anchor='w')

        # Label for displaying "Last SKU scanned"
        self.last_SKU_label = tk.Label(control_frame, text="Last SKU scanned: ", font=('Arial', 14))
        self.last_SKU_label.pack(side=tk.TOP, padx=5, pady=5, anchor='w')

        # style = ttk.Style()
        # style.configure("NoBorder.Treeview", borderwidth=0)

        # Treeview setup for displaying data without borders
        self.tree_view = ttk.Treeview(control_frame, columns=('Time', 'SKU', 'To Scan', 'ModelPart', 'Line', 'Category'), show='headings', style="NoBorder.Treeview")
        for col in self.tree_view["columns"]:
            self.tree_view.heading(col, text=col, anchor='center')
            self.tree_view.column(col, stretch=tk.YES)
            
        self.tree_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.text_box = tk.Text(control_frame, height=20, width=50, padx=5, pady=5, bd=0, highlightthickness=0)
        self.text_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Button for toggling the scanning process with extra padding for separation
        self.start_stop_btn = tk.Button(control_frame, text='Start Scanning', command=self.toggle_scanning, font=('Arial', 14))
        self.start_stop_btn.pack(side=tk.BOTTOM, pady=10, padx=5, anchor='center')

        # Label for displaying the image, dynamically resized with the frame
        self.image_label = tk.Label(image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Centering frames within the grid
        control_frame.grid_rowconfigure(0, weight=1)
        control_frame.grid_columnconfigure(0, weight=1)
        image_frame.grid_rowconfigure(0, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)
        
    def run(self):
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()

    def exists_in_database(self, scanned_item):
        if scanned_item:
            print(f'{scanned_item} found in Database')
            return scanned_item
        else:
            return

    def terminate_process(self):
        os._exit(1)

    def on_closing(self):
        #"""Handle the application close event."""
        if messagebox.askokcancel("Quit", "Do you want to exit the application?"):
            if hasattr(self, 'scan'):
                self.scan.stop()  # Assuming there's a method to stop the scanning process
                self.terminate_process()
            self.destroy()

    def update_pid_label(self):
        if self.PID is not None:
            self.current_pid_label.config(text=f"Current PID: {self.PID}", fg="green")
        else:
            self.current_pid_label.config(text="Current PID: None", fg="red")

    def update_SKU_label(self):
        if self.SKU is not None:
            self.last_SKU_label.config(text=f"Last SKU scanned: {self.SKU}", fg="green")
        else:
            self.last_SKU_label.config(text="Last SKU scanned: None", fg="red")
