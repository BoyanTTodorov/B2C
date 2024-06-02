import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from database import DatabaseManager
from scanner_worker import ScannerWorker
from datetime import datetime
import requests
from PIL import Image, ImageTk
from io import BytesIO
from tkinter import messagebox
from functools import partial

# Disable warning 
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import Logging to trace the issue
import logging

class App(ttk.Window):
    def __init__(self, username, theme='lumen'):
        super().__init__(themename=theme)

        self.username = username
        self.title('Quality Control Application')
        self.scan_state = 1  
        self.scanned_data = {'PID': None,'SKU': None, 'GRADE': None, 'HD': None}  
        self.photo = None  
        self.geometry('1700x520')
        self.attributes('-alpha', 0.9)  

        self.pid = None
        self.scu = None

        self.db = DatabaseManager(self.username)

        self.scan = ScannerWorker()
        self.scan.set_on_scan_callback(self.handle_scan)
        self.scan.set_display_message_callback(self.display_message)
        self.scan.start()
        self.initialize_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)   

    def initialize_ui(self):
        style = ttk.Style()
        style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))  

        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        image_frame = ttk.Frame(self)
        image_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        self.configure_treeview(control_frame)
        self.configure_text_log(control_frame)
        self.configure_image_display(image_frame)
        
        self.create_input_and_button(control_frame)

        self.display_message("Welcome to the QC application! Please start by scanning\nPICKID, SKU, GRADE, HD. 📦", color='green')

    def create_input_and_button(self, parent):
        input_frame = ttk.Frame(parent)
        input_frame.pack(side='bottom', pady=10)

        close_state_label = ttk.Label(input_frame, text="Manually Changing state to CLOSED please enter HD:")
        close_state_label.grid(row=0, column=0, padx=5)

        input_entry = ttk.Entry(input_frame, width=20)
        input_entry.grid(row=0, column=1, padx=5)

        update_button = ttk.Button(input_frame, text="Close HD", command=lambda entry=input_entry: self.update_close_state(entry))
        update_button.grid(row=0, column=2, padx=5)

        show_open_HD = ttk.Button(input_frame, text="Show HD", command=self.show_qc)
        show_open_HD.grid(row=0, column=3, padx=5)

    def show_qc(self):
        # Create a new window
        qc_window = ttk.Window(themename='lumen')
        qc_window.title("Open HDs")
        qc_window.attributes('-alpha', 0.9)  

        # Add a Treeview widget
        tree = ttk.Treeview(qc_window, columns=("id","ctime", "pickid", "scu", "qty", "cuser", "hd", "grade", "item_type", "state", "line", "modelpart"), show='headings')
        tree.heading("id", text="id")
        tree.heading("ctime", text="ctime")
        tree.heading("pickid", text="pickid")
        tree.heading("scu", text="scu")
        tree.heading("qty", text="qty")
        tree.heading("cuser", text="cuser")
        tree.heading("hd", text="hd")
        tree.heading("grade", text="grade")
        tree.heading("item_type", text="item_type")
        tree.heading("state", text="State")
        tree.heading("line", text="line")
        tree.heading("modelpart", text="modelpart")
        tree.pack(fill=ttk.BOTH, expand=True)

        # Function to populate the Treeview with data
        def populate_tree():
            # Clear the existing data in the Treeview
            for item in tree.get_children():
                tree.delete(item)

            for col in tree['columns']:
               tree.heading(col, text=col)
               tree.column(col, anchor='center', width=100)
            
            # Populate the Treeview with new data
            data = self.db.get_QC_data()
            data = [list(i) for i in data]
            for row in data:
                tree.insert("", "end", values=row)

        def refresh_data():
            # Clear existing items in the Treeview
            tree.delete(*tree.get_children())
            
            # Fetch data from the database
            data = self.db.get_QC_data()
            data = [list(i) for i in data]
            # Insert each row of data into the Treeview
            for row in data:
                tree.insert("", "end", values=row)
        
        # Schedule the next refresh after 2 seconds
        qc_window.after(2000, refresh_data)

        # Add a button to delete selected entry
        delete_button = ttk.Button(qc_window, text="Delete Selected", command=lambda: self.delete_selected(tree))
        delete_button.pack(side="left", padx=5, pady=5)

        # Add a button to manually refresh data
        refresh_button = ttk.Button(qc_window, text="Refresh", command=populate_tree)
        refresh_button.pack(side="left", padx=5, pady=5)

        # Populate the Treeview initially
        populate_tree()

    def delete_selected(self, tree):
        selected_items = tree.selection()

        if not selected_items:
            print("No item selected for deletion.")
            return

        selected_item = selected_items[0]
        print(selected_items)
        hd = tree.item(selected_item, 'values')[0]
        
        # Delete the item from the database
        result = self.db.delete_entry(hd)
        if result:
            print(f"Deleted item with HD: {hd} from the database.")
        else:
            print(f"Failed to delete item with HD: {hd} from the database.")

        # Remove the item from the Treeview
        tree.delete(selected_item)

    def update_close_state(self, entry):
        close_state = entry.get().strip()

        if len(close_state) == 18:
            message = self.db.manualy_close_hd(close_state)
            if message:
                self.display_message(f"❌ {message}", color='red')
            else:
                self.display_message(f"✅ HD {close_state} successfully closed.", color='green')
                # Clear the input box
                entry.delete(0, 'end')
                # Clear the input box
                self.clear_input_box()
                return
        else:
            self.display_message("❌ Wrong HD!", color='red')
            # Clear the input box
            entry.delete(0, 'end')
            return

    def configure_treeview(self, parent):
        self.tree = ttk.Treeview(parent, columns=('ID', 'CTIME', 'PICKID','SKU', 'QTY', 'CUSER', 'MODEL', 'LINE', 'TYPE', 'GRADE', 'HD'), show='headings')
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center', width=120)

        # Configure a tag for white text color
        self.tree.tag_configure('white_text', foreground='black')
        self.tree.pack(expand=True, fill='both')

    def configure_text_log(self, parent):
        self.text_box = ttk.Text(parent, height=10, state='disabled')
        # Configure text color tags
        self.text_box.tag_configure('error', foreground='red', font=('Helvetica', 12, 'bold'))  # Error messages in bold red
        self.text_box.tag_configure('info', foreground='black', font=('Helvetica', 12))  # Regular messages in black
        self.text_box.pack(expand=True, fill='both')

    def configure_image_display(self, parent):
        self.image_label = ttk.Label(parent)
        self.image_label.pack(fill='both', expand=True)

    def display_message(self, message_info,color = 'black'):
        # Unpack the message and color from the message_info tuple
        message = message_info
        color = color
        self.text_box.config(state='normal')
        
        # Format the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create the full message string with the timestamp
        message_with_time = f"{current_time} - {message}\n"
        
        # Configure tags for different message styles based on the color
        self.text_box.tag_configure('info', foreground='black', font=('Helvetica', 12))
        self.text_box.tag_configure('error', foreground='red', font=('Helvetica', 12, 'bold'))
        self.text_box.tag_configure('success', foreground='green', font=('Helvetica', 12, 'bold'))
        self.text_box.tag_configure('info', foreground='orange', font=('Helvetica', 12, 'bold'))
        # Insert the message into the text box with the appropriate tag
        if color == 'red':
            self.text_box.insert('end', message_with_time, 'error')
        elif color == 'green':
            self.text_box.insert('end', message_with_time, 'success')
        else:
            self.text_box.insert('end', message_with_time, 'info')
        
        # Scroll to the end of the text box to ensure the latest message is visible
        self.text_box.see('end')
        
        # Set the text box to disabled to prevent user edits
        self.text_box.config(state='disabled')

    def load_data(self):
        try:
            if self.scanned_data['SKU']:  
                query = f"SELECT * FROM R710KZDA.RECEIVING WHERE SKU = '{self.scanned_data['SKU']}' LIMIT 1"
                columns, data = self.db.get_data(query)

                if not data:
                    self.display_message("❌ Error: No data found for the scanned SKU. Please scan a valid SKU.", color='red')
                    return False
                else:
                    self.tree.delete(*self.tree.get_children())  # Clear existing data

                    # Populate the treeview with data using the 'white_text' tag
                    for row in data:
                        formatted_row = [col.strftime('%Y-%m-%d %H:%M:%S') if isinstance(col, datetime) else col for col in row]

                        temp = formatted_row[5]
                        formatted_row.pop(5)
                        formatted_row.insert(2, temp)
                    
                        self.tree.insert('', 'end', values=formatted_row, tags=('white_text',))
                    return True
        except Exception as e:
            self.display_message(f"❌ Error occurred while loading data: {str(e)}", color='red')
            return False

    def update_data(self):
        # Update the database record with the new GRADE and HU
        try:
            if self.scanned_data['PID'] and self.scanned_data['SKU'] and self.scanned_data['GRADE'] and self.scanned_data['HD']:
                new_columns = self.db.get_new_data(self.scanned_data['SKU'])
                #print(new_columns)
                item_type = new_columns[3].strip()
                line = new_columns[2]
                modelpart = new_columns[1]
                msg = self.db.update_record(self.scanned_data['PID'], self.scanned_data['SKU'], self.scanned_data['GRADE'], self.scanned_data['HD'], item_type, line, modelpart)
                #print(f'BEFORE INSERT:{pid, self.scanned_data['SKU'], self.scanned_data['GRADE'], self.scanned_data['HD'], item_type, line, modelpart}')
                self.display_message(msg)
                #self.load_data()
                # Reset scanned data
                self.scanned_data = {'PID':None,'SKU': None, 'GRADE': None, 'HD': None}
        except Exception as e:
            self.display_message(f"❌ Error occurred while updating data: {str(e)}.", color='red')

    def handle_scan(self, code, code_type):
        last_state = self.scan_state
        try:
            if self.scan_state == 1:
                if len(code) != 8:           
                    error_message = "❌ Error: Invalid PICKID format. Please scan again with a valid PICKID."
                    self.display_message(error_message, color='red')
                    return
                elif len(code) == 8 and self.db.check_for_pickid(code)[0] == code:
                    self.scanned_data['PID'] = code 
                    self.pid = code
                    self.display_message(f"✅ PICKID: {self.scanned_data['PID']} scanned successfully.", color='green')
                    self.display_message("🔍 NEXT STEP SCAN SKU!", color='orange')
                    self.scan_state = 2
                else:
                    self.scan_state = 1
                    error_message = "❌ Please start with valid PICKID."
                    self.display_message(error_message, color='red')

            elif self.scan_state == 2:
                self.load_and_display_image(code)
                if len(code) != 13:
                    error_message = "❌ Error: Invalid SKU format. Please scan again with a valid SKU."
                    self.display_message(error_message, color='red')
                    return

                qty_receiving = self.get_scu_qty_receiving(code)
                qty_sorting = self.get_scu_qty_sorting(code)


                if qty_receiving <= qty_sorting:
                    error_message = "❌ Error: SKU cannot be processed as received quantity is not greater than sorted quantity.\nStart scanning with PICKID"
                    self.display_message(error_message, color='red')
                    self.scan_state == 1
                    return
                
                self.scanned_data['SKU'] = code
                self.scu = code
                sku_for_pid = self.db.check_scu_for_pid(self.scu, self.pid)

                if sku_for_pid is None:
                    self.display_message(f"❌ SKU: {self.scanned_data['SKU']} doesnt belong to PICKID:{self.pid}.", color='red')
                    self.display_message("🔍 PLEASE SCAN CORRECT SCU", color='orange')
                    self.scan_state = 2  # Move to next state only after successful load
                    return 
                
                if self.load_data():  # Proceed only if data is successfully loaded
                    self.display_message(f"✅ SKU: {self.scanned_data['SKU']} scanned successfully.", color='green')
                    self.display_message("🔍 NEXT STEP SCAN GRADE!", color='orange')
                    self.scan_state = 3  # Move to next state only after successful load
                else:
                    return  # Stay in the current state if no data found

            elif self.scan_state == 3:
                if int(code) not in [1, 2, 3]:
                    error_message = "❌ Error: Invalid GRADE format. Please scan again with a valid GRADE (1, 2, or 3)."
                    self.display_message(error_message, color='red')
                    self.scan_state = 3
                    return
                else:
                    self.scanned_data['GRADE'] = int(code)
                    self.tree.set(self.tree.get_children()[-1], 'GRADE', self.scanned_data['GRADE'])
                    self.display_message(f"✅ GRADE: {self.scanned_data['GRADE']} scanned successfully.",color='green')
                    self.display_message("🔍 NEXT STEP SCAN HD!", color='orange')
                    self.scan_state = 4

            elif self.scan_state == 4:
                if len(code) != 18:
                    error_message = "❌ Error: Invalid HD format. Please scan again with a valid HD (18 characters)."
                    self.display_message(error_message, color='red')
                    self.scan_state = 4
                    return
                self.scanned_data['HD'] = code
                self.tree.set(self.tree.get_children()[-1], 'HD', self.scanned_data['HD'])
                self.display_message(f"✅ HD:{self.scanned_data['HD']} scanned successfully.", color='green')
                self.update_data()
                #self.load_data()  # Load updated data after database update
                self.scan_state = 1  # Reset for the next item
        except Exception as e:
            self.scan_state = last_state
            self.display_message("❌ Error occurred while handling scan, \nPLEASE RESCAN STARTING WITH PICKID,\nSystem Error.", color='red')

    def get_scu_qty_receiving(self, scu):
        # Simulate a database call to get the receiving quantity
        query = f"SELECT COUNT(*) FROM R710KZDA.RECEIVING WHERE SKU = '{scu}'"
        _, qty = self.db.get_data(query)
        
        return qty[0][0] if qty and qty[0] else 0

    def get_scu_qty_sorting(self, scu):
        # Simulate a database call to get the sorting quantity
        query = f"SELECT COUNT(*) FROM R710KZDA.SORTING WHERE SKU = '{scu}'"
        _, qty = self.db.get_data(query)
       
        return qty[0][0] if qty and qty[0] else 0

    def load_and_display_image(self, scu):
        result = self.db.get_model_link_line_category(scu)
        if result:
            link = result[0].strip()
            if link:
                self.display_image(link)
            else:
                self.display_message_img("No image available for this SKU.")
        else:
            self.display_message_img("No data or image available for this SKU.")

    def display_image(self, image_url):
        try:
            response = requests.get(image_url, verify=False)  # For demonstration; disable SSL verification
            
            if response.status_code == 200:
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize((360, 480))  # Resize the image if necessary
                self.photo = ImageTk.PhotoImage(image=img, master=self) # Store the image in a PhotoImage object

                # Configure the image label with the new PhotoImage object
                self.image_label.config(image=self.photo)
                self.image_label.image = self.photo  # Maintain a reference to the PhotoImage object
            else:
                logging.error(f"Failed to load image from {image_url}. HTTP status code: {response.status_code}")
                self.display_message_img("Failed to load image: HTTP error")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to make a request to {image_url}: {e}")
            self.display_message_img(f"Failed to load image: {str(e)}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading image: {str(e)}")
            self.display_message_img(f"Failed to load image: {str(e)}")

    def display_message_img(self, message):
        self.image_label.config(text=message, image=None)  # Display the message

    def on_close(self):
        """Handle the application close event."""
        if messagebox.askokcancel("Quit", "Do you want to exit the application?"):
            if hasattr(self, 'scan'):
                self.scan.stop()  # Assuming there's a method to stop the scanning process
            self.destroy()


def validate_username(username):
    # Custom validation function to check if the username contains only letters and numbers
    return username.isalnum()

def start_login_window():
    # Initialize the root window with the 'lumen' theme
    window = ttk.Window(themename='lumen')
    window.geometry('300x180')
    window.title('Login')
    window.attributes('-alpha', 0.9)  

    def login():
        username = inp_username.get().strip()
        if username:
            if validate_username(username):
                window.withdraw()
                app = App(username)
                app.protocol("WM_DELETE_WINDOW", partial(on_close, app, window))
                app.mainloop()
            else:
                messagebox.showerror("Login Failed", "Incorrect username format. Please use only letters and numbers.")
        else:
            messagebox.showerror("Login Failed", "Please enter a username")

    lbl_username = ttk.Label(window, text='Reflex Username:')
    lbl_username.pack(pady=(20, 10))
    vcmd = (window.register(validate_username), '%P')
    inp_username = ttk.Entry(window, validate="key", validatecommand=vcmd)
    inp_username.pack()

    btn_login = ttk.Button(window, text='Login', command=login)
    btn_login.pack(pady=20)

    def on_close(app, login_window):
        app.destroy()
        login_window.destroy()

    window.mainloop()

def main():
    start_login_window()

if __name__ == '__main__':
    main()

