import pyodbc
from user_credential import user, password
# QC

class DatabaseManager:
    def __init__(self, username):
        self.username = username

    def connect(self):
        conn_str = (f"DRIVER={{Client Access ODBC Driver (32-bit)}};"
                    "System=X"
                    "Port=X;"
                    f"uid={user};"
                    f"pwd={password};"
                    "Database=X")
        return pyodbc.connect(conn_str)

    def get_data(self, query):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return columns, rows

    def update_record(self, pickid, SKU_code, grade, hd, item_type, line, modelpart, state='open'):
        # Define maximum SKUs per hd for each item type
        max_SKUs = {
            'VA': 2,
            'VB': 3,
            'VC': 60,
            'VG': 20,
            'VO': 7
        }

        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                # Check if an open HD with the same grade and item type exists
                cursor.execute("""
                    SELECT hd FROM R710KZDA.SORTING
                    WHERE hd != ? AND grade = ? AND item_type = ? AND state = 'open'
                """, (hd, grade, item_type))
                existing_hd = cursor.fetchone()
                if existing_hd:
                    return f"An open HD with the same grade '{grade}' and item type '{item_type}' already exists: {existing_hd[0]}."
        
                # Check if the hd is closed
                cursor.execute("""
                    SELECT state FROM R710KZDA.SORTING WHERE hd = ?
                """, (hd,))
                current_state = cursor.fetchone()
                if current_state and current_state[0] == 'closed':
                    return 'Operation aborted: HD has been closed and cannot accept more SKUs.'
                
                # # Check if hd, grade, and item_type match with existing records
                # cursor.execute("""
                #     SELECT * FROM R710KZDA.SORTING WHERE grade = ? OR item_type != ? AND STATE = 'open'
                # """, (grade, item_type))
                mismatched_records = cursor.fetchall()
                # if mismatched_records:
                #     formatted_results = "\n".join([f"HD: {row[6]}, Grade: {row[7]}, Item Type: {row[8]}" for row in mismatched_records])
                #     return f"Operation aborted: GRADE MISMATCH ERROR. Conflicting records:\n{formatted_results}"
                # # Check if hd, grade, and item_type match with existing records
                # cursor.execute("""
                #     SELECT * FROM R710KZDA.SORTING WHERE grade != ? OR item_type = ? AND STATE = 'open'
                # """, (grade, item_type))
                # mismatched_records = cursor.fetchall()
                if mismatched_records:
                    try:
                        # Check if hd, grade, and item_type match with existing records
                        cursor.execute("""
                            SELECT * FROM R710KZDA.SORTING WHERE grade = ? OR item_type != ? AND STATE = 'open'
                        """, (grade, item_type))
                        mismatched_records = cursor.fetchall()
                        if mismatched_records:
                            formatted_results = "\n".join([f"HD: {row[6]}, Grade: {row[7]}, Item Type: {row[8]}" for row in mismatched_records])
                            return f"Operation aborted: GRADE MISMATCH ERROR. Conflicting records:\n{formatted_results}"
                        # Check if hd, grade, and item_type match with existing records
                        cursor.execute("""
                            SELECT * FROM R710KZDA.SORTING WHERE grade != ? OR item_type = ? AND STATE = 'open'
                        """, (grade, item_type))
                        mismatched_records = cursor.fetchall()

                    except Exception as e:
                            return f'Exception occure {e}'
                    formatted_results = "\n".join([f"HD: {row[6]}, Grade: {row[7]}, Item Type: {row[8]}" for row in mismatched_records])
                    return f"Operation aborted: ITEM_TYPE MISMATCH ERROR. Conflicting records:\n{formatted_results}"

                # Check if hd, grade, and item_type match with existing records
                cursor.execute("""
                    SELECT * FROM R710KZDA.SORTING WHERE hd = ? AND (grade != ? OR item_type != ?) AND STATE = 'open'
                """, (hd, grade, item_type))
                mismatched_records = cursor.fetchall()
                if mismatched_records:
                    formatted_results = "\n".join([f"HD: {row[6]}, Grade: {row[7]}, Item Type: {row[8]}" for row in mismatched_records])
                    return f"Operation aborted: GRADE or ITEM TYPE MISMATCH ERROR. Conflicting records:\n{formatted_results}"

                # Check SKU count for the hd
                cursor.execute("""
                    SELECT COUNT(*) AS SKU_count FROM R710KZDA.SORTING
                    WHERE item_type = ? AND grade = ? AND hd = ? AND state = 'open'
                    GROUP BY hd
                """, (item_type, grade, hd))
                record = cursor.fetchone()

                # Process existing hd or handle the situation when no suitable hd is available
                if record:
                    SKU_count = record[0]
                    if SKU_count >= max_SKUs[item_type]:
                        return f'Cannot insert: HD {hd} has already reached its maximum limit of {max_SKUs[item_type]} SKUs for {item_type}.'
                else:
                    # Handle the case when no suitable open hd exists
                    if state != 'open':
                        return 'No open hd available and not permitted to open a new one. Cannot insert.'

                # Insert new SKU record into the database
                cursor.execute("""
                    INSERT INTO R710KZDA.SORTING
                    (CTIME, PICKID, SKU, QTY, CUSER, hd, GRADE, ITEM_TYPE, STATE, LINE, MODELPART)
                    VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pickid, SKU_code, 1, self.username, hd, grade, item_type, state, line, modelpart))
                conn.commit()

                # Check if the hd is now full
                if record and SKU_count + 1 == max_SKUs[item_type]:
                    # Update the hd's state to 'closed'
                    cursor.execute("""
                        UPDATE R710KZDA.SORTING SET STATE = 'closed' WHERE hd = ?
                    """, (hd,))
                    conn.commit()
                    return f'HD {hd} has reached its maximum capacity and is now closed.'
                else:
                    return f'Successfully inserted data into HD {hd}.'

        except Exception as e:
            return f'Error in updating record: {e}'

        
    def manualy_close_hd(self, hd):
        # First, check if the HD exists and is in an open state
        check_query = "SELECT STATE FROM R710KZDA.SORTING WHERE HD = ?"
        update_query = "UPDATE R710KZDA.SORTING SET STATE = 'closed' WHERE HD = ?"

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(check_query, (hd,))
                result = cursor.fetchone()

                if result and result[0] == 'open':
                    cursor.execute(update_query, (hd,))
                    conn.commit()
                    return f"HD {hd} successfully closed."
                else:
                    return f"HD {hd} does not exist or is not in an open state."
        except pyodbc.Error as e:
            return f"Error executing SQL query: {e}"

    def get_new_data(self, SKU):
        query = "SELECT pickid, modelpart, line, category FROM R710KZDA.RECEIVING WHERE SKU = ?"
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (SKU,))
            return cursor.fetchone()  # Fetches the first row of a query result or None if no data is found.

    def get_model_link_line_category(self, SKU):
        query = '''
                SELECT  
                    TRIM('https://X' || SUBSTR(AICODI, 1, 6) || SUBSTR(AICODI, 13, 5) || '-' || SUBSTR(AICODI, 18, 5)) AS link
                FROM wcstst_dat.gnarcap
                WHERE aicart = ?
                '''
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (SKU,))
            return cursor.fetchone()

    def set_db_callback(self, callback):
        self.set_db_callback = callback


    def check_for_pickid(self, pickid):
            query = "SELECT pickid FROM R710KZDA.RECEIVING WHERE pickid = ?"

            try:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (pickid,))
                    data = cursor.fetchone()
                    if data:
                        # If data exists, return it
                        print(data)
                        return data
                    else:
                        # If no data found, return a specific value indicating no data
                        return "No data found for the specified pickid."
            except Exception as e:
                # Return an error message if an exception occurs
                return f'Exception occurred: {e}'

    # def check_for_return_value(self, hd, grade, item_type):
    #     conn, cursor = self.connect()
    #             # Check if an open HD with the same grade and item type exists
    #     cursor.execute("""
    #         SELECT hd FROM R710KZDA.SORTING
    #         WHERE hd != ? AND grade = ? AND item_type = ? AND state = 'open'
    #     """, (hd, grade, item_type))
    #     existing_hd = cursor.fetchone()
    #     if existing_hd:
    #         return f"An open HD with the same grade '{grade}' and item type '{item_type}' already exists: {existing_hd[0]}."

    def check_scu_for_pid(self, sku, pid):
        query = "SELECT PICKID, SKU FROM R710KZDA.RECEIVING WHERE SKU = ? AND PICKID = ?"

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (sku, pid))
                data = cursor.fetchone()
                if data:
                    # If data exists, return it
                    return data
                # else:
                #     # If no data found, return a specific value indicating no data
                #     return None
        except Exception as e:
            # Return an error message if an exception occurs
            return f'Exception occurred: {e}'
        
    def get_QC_data(self):
        query = "SELECT * FROM R710KZDA.SORTING WHERE state = 'open'"
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()  # Fetches all rows of a query result

    def delete_entry(self, id):
        query = "DELETE FROM R710KZDA.SORTING WHERE id = ?"
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (id,))
                conn.commit()
                return f"ID {id} successfully deleted."
        except pyodbc.Error as e:
            return f"Error deleting HD {id}: {e}"
      