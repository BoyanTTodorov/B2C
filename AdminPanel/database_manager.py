import pyodbc
import getpass
from user_credential import user, password

class DatabaseManager:
    def __init__(self):
        self.username = getpass.getuser()

    def connect(self):
        conn_str = (f"DRIVER={{Client Access ODBC Driver (32-bit)}};"
                    f"System=X"
                    f"Port=X;"
                    f"uid={user};"
                    f"pwd={password};"
                    "Database=X;")
        return pyodbc.connect(conn_str)

    def execute_query(self, query, params=None, commit=False):
        with self.connect() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
                print(cursor.description)

            else:
                cursor.execute(query)
            if commit:
                conn.commit()
            else:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                return columns, rows

    def get_data(self, query):
        return self.execute_query(query)

    def insert_data(self, query, params):
        self.execute_query(query, params, True)

    def update_data(self, query, params):
        self.execute_query(query, params, True)

    def remove_data(self, query, params):
        self.execute_query(query, params, True)
