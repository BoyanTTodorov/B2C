import tkinter as tk
from tkinter import ttk
from database_manager import DatabaseManager
from datetime import datetime
import csv
from custom_messagebox import CustomMessageBox

class App(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.checkbox_states = {}
        self.setup_ui()
        
    def setup_ui(self):
        self.pack(fill='both', expand=True, padx=10, pady=10)
        style = ttk.Style()
        style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))
        style.configure('TButton', font=('Helvetica', 10))

        queries = [
            ('Receiving', 'SELECT * FROM R710KZDA.RECEIVING'),
            ('Errors', 'SELECT * FROM R710KZDA.ERRORS'),
            ('Sorting', 'SELECT * FROM R710KZDA.SORTING'),
            ('Shipping', 'SELECT * FROM R710KZDA.SHIPPING'),
            ('Labels', 'SELECT * FROM R710KZDA.LABELS')
        ]
        self.tabs = ttk.Notebook(self)
        for name, query in queries:
            frame = ttk.Frame(self.tabs)
            self.tabs.add(frame, text=name)
            self.create_treeview(frame, query)
        self.tabs.pack(expand=True, fill='both')

        self.create_search_area()

    def create_treeview(self, parent, query):
        columns, data = self.db.get_data(query)
        columns = ["Select"] + columns
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        tree.heading("#1", text="Select")
        tree.column("#1", width=20, anchor='center')
        for i, col in enumerate(columns[1:], start=1):
            tree.heading(i, text=col)
            tree.column(i, width=110, anchor='center')  # Set anchor to center
        for row in data:
            row_id = tree.insert('', tk.END, values=(' ',) + tuple(row))
            self.checkbox_states[row_id] = ' '
        tree.grid(row=0, column=0, sticky='nsew')
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        sb_v = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        sb_v.grid(row=0, column=1, sticky='ns')
        tree.configure(yscrollcommand=sb_v.set)

        # Bind the toggle_checkbox method to the Treeview
        tree.bind('<Button-1>', lambda event: self.toggle_checkbox(tree, event))

        # Buttons at the bottom
        self.add_buttons(parent, tree, query)

    def create_search_area(self):
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', pady=10)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(search_frame, text="Start Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=(0, 10))
        self.start_date_entry = ttk.Entry(search_frame)
        self.start_date_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(search_frame, text="End Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=(0, 10))
        self.end_date_entry = ttk.Entry(search_frame)
        self.end_date_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(search_frame, text="Search", command=self.search_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(search_frame, text="Report 1", command=self.generate_report_1).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(search_frame, text="Report 2", command=self.generate_report_2).pack(side=tk.LEFT, padx=(0, 10))

    def add_buttons(self, parent, tree, query):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky='ew')

        ttk.Button(button_frame, text='Add', command=lambda: self.show_insert_form(tree, query.split(' FROM ')[1].split()[0])).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Update', command=lambda: self.show_update_form(tree, query.split(' FROM ')[1].split()[0])).pack(side=tk.LEFT, padx=5) #state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Delete', command=lambda: self.delete_selected(tree, query)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Refresh', command=lambda: self.refresh_treeview(tree, query)).pack(side=tk.LEFT, padx=5)

    def search_data(self):
        search_term = self.search_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()

        active_tab = self.tabs.tab(self.tabs.select(), "text")
        query = next(query for name, query in [
            ('Receiving', 'SELECT * FROM R710KZDA.RECEIVING'),
            ('Errors', 'SELECT * FROM R710KZDA.ERRORS'),
            ('Sorting', 'SELECT * FROM R710KZDA.SORTING'),
            ('Shipping', 'SELECT * FROM R710KZDA.SHIPPING'),
            ('Labels', 'SELECT * FROM R710KZDA.LABELS')
        ] if name == active_tab)

        if start_date and end_date:
            query += f" WHERE DATE_COLUMN BETWEEN '{start_date}' AND '{end_date}'"

        columns, data = self.db.get_data(query)
        filtered_data = [row for row in data if search_term in map(str, row)]
        
        for tab in self.tabs.winfo_children():
            for widget in tab.winfo_children():
                if isinstance(widget, ttk.Treeview):
                    tree = widget
                    tree.delete(*tree.get_children())
                    for row in filtered_data:
                        tree.insert('', tk.END, values=(' ',) + tuple(row))

    def generate_report_1(self):
        query = "SELECT * FROM R710KZDA.RECEIVING"
        columns, data = self.db.get_data(query)
        with open('report_1.txt', 'w') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(columns)
            writer.writerows(data)
        CustomMessageBox.show_info("Success", "Report 1 saved as report_1.txt")

    def generate_report_2(self):
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()

        if not start_date or not end_date:
            CustomMessageBox.show_error("Error", "Please provide a start and end date for Report 2.")
            return

        query = f"SELECT * FROM R710KZDA.OUTBOUND WHERE DATE_COLUMN BETWEEN '{start_date}' AND '{end_date}'"
        columns, data = self.db.get_data(query)
        with open('report_2.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(data)
        CustomMessageBox.show_info("Success", "Report 2 saved as report_2.csv")

    def show_insert_form(self, tree, base_table):
        top = tk.Toplevel(self)
        top.title("Insert Data")
        entries = {}

        try:
            columns, _ = self.db.get_data(f"SELECT * FROM {base_table} WHERE 1=0")
            for idx, column in enumerate(columns):
                if column != 'ID':
                    ttk.Label(top, text=column).grid(row=idx, column=0)
                    entry = ttk.Entry(top)
                    if column == 'CTIME':  # Automatically set the current timestamp for CTIME
                        entry.insert(0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        entry.config(state='readonly')  # Optionally make it read-only
                    entry.grid(row=idx, column=1)
                    entries[column] = entry

            ttk.Button(top, text="Submit", command=lambda: self.insert_data(top, base_table, entries)).grid(row=len(columns), column=1)

        except Exception as e:
            CustomMessageBox.show_error("Error", f"Failed to open form: {e}")
            top.destroy()

    def insert_data(self, top, base_table, entries):
        # Prepare entries dict to ensure values are appropriate
        entries = {key: entry.get() for key, entry in entries.items() if entry.get()}  # Remove empty entries
        if 'CTIME' in entries:
            # Ensure the CTIME is formatted properly
            entries['CTIME'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        columns = ', '.join(entries.keys())
        placeholders = ', '.join(['?' for _ in entries])
        values = tuple(entries.values())
        insert_query = f"INSERT INTO {base_table} ({columns}) VALUES ({placeholders})"

        try:
            self.db.insert_data(insert_query, values)
            CustomMessageBox.show_info("Success", "Data inserted successfully.")
            top.destroy()  # Close the insert window after successful operation
        except Exception as e:
            CustomMessageBox.show_error("Error", str(e))
            # Do not destroy 'top' if there's an error, so user can correct and resubmit

    def show_update_form(self, tree, base_table):
        selected_item = tree.selection()
        if not selected_item:
            CustomMessageBox.show_info("Error", "No item selected for updating.")
            return
        
        top = tk.Toplevel(self)
        top.title("Update Data")
        entries = {}

        try:
            selected_item = selected_item[0]
            current_values = tree.item(selected_item, 'values')[1:]  # Exclude checkbox
            columns, _ = self.db.get_data(f"SELECT * FROM {base_table} WHERE 1=0")  # Remove [0] index here

            if not columns:
                raise Exception("No columns found. Check database connection and table name.")

            for idx, (column, value) in enumerate(zip(columns, current_values)):
                if column != 'ID':
                    ttk.Label(top, text=column).grid(row=idx, column=0)
                    entry = ttk.Entry(top)
                    entry.insert(0, value)
                    entry.grid(row=idx, column=1)
                    entries[column] = entry

            ttk.Button(top, text="Update", command=lambda: self.update_data(tree, top, selected_item, base_table, entries)).grid(row=len(columns), column=1)

        except Exception as e:
            CustomMessageBox.show_error("Error", f"Failed to populate form: {e}")
            top.destroy()

    def update_data(self, tree, top, selected_item, base_table, entries):
        # Prepare entries dict to ensure values are appropriate
        entries = {key: entry.get() for key, entry in entries.items() if entry.get()}  # Remove empty entries
        if 'CTIME' in entries:
            # Ensure the CTIME is formatted properly
            entries['CTIME'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        item_id = tree.item(selected_item, 'values')[1]  # Assuming ID is the first column after checkbox
        set_clause = ', '.join([f"{key} = ?" for key in entries])
        params = tuple(entries.values()) + (item_id,)  # Add item_id as the last parameter
        update_query = f"UPDATE {base_table} SET {set_clause} WHERE ID = ?"

        try:
            self.db.update_data(update_query, params)
            CustomMessageBox.show_info("Success", "Data updated successfully.")
            top.destroy()  # Close the update window after successful operation
        except Exception as e:
            CustomMessageBox.show_error("Error", str(e))
            # Do not destroy 'top' if there's an error, so user can correct and resubmit

    def delete_selected(self, tree, query):
        selected_items = [item for item in tree.get_children() if tree.set(item, '#1') == '✓']
        if not selected_items:
            CustomMessageBox.show_info("Error", "No items selected for deletion.")
            return
        base_table = query.split(' FROM ')[1].split()[0]
        for item in selected_items:
            primary_key_value = tree.item(item, "values")[1]  # Assuming ID is the first column after checkbox
            delete_query = f"DELETE FROM {base_table} WHERE ID = ?"
            try:
                self.db.remove_data(delete_query, (primary_key_value,))
                tree.delete(item)
            except Exception as e:
                CustomMessageBox.show_error("Error", str(e))
        CustomMessageBox.show_info("Success", "Selected items deleted successfully.")

    def refresh_treeview(self, tree, query):
        columns, data = self.db.get_data(query)
        tree.delete(*tree.get_children())  # Clear existing data
        for row in data:
            row_id = tree.insert('', tk.END, values=(' ',) + tuple(row))
            if row_id in self.checkbox_states:
                tree.set(row_id, "#1", self.checkbox_states[row_id])
            else:
                tree.set(row_id, "#1", ' ')

    def toggle_checkbox(self, tree, event):
        try:
            region = tree.identify_region(event.x, event.y)
            if region == "cell":
                col = tree.identify_column(event.x)
                if col == "#1":
                    row_id = tree.identify_row(event.y)
                    current_value = tree.set(row_id, "#1")  
                    new_value = '✓' if current_value != '✓' else ' '
                    tree.set(row_id, "#1", new_value)
                    self.checkbox_states[row_id] = new_value  # Store checkbox state
        except Exception as e:
            self.message_field.config(text=str(e))
