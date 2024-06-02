import pyodbc
from user_credential import user, password
from datetime import datetime
# import logging

class DatabaseManager:
    def __init__(self, username):
        # logging.basicConfig(level=logging.DEBUG, filename='database_log.log', filemode='a',
        #             format='%(asctime)s - %(levelname)s - %(message)s')
        self.ctime = datetime.now()
        #self.logger = logging.getLogger(__name__)
        self.username = username
        self.sku = None
    def connect(self):
        try:
            # Establish connection
            conn = pyodbc.connect('''DRIVER={Client Access ODBC Driver (32-bit)};
                System=X;
                Port=X;
                '''f'''uid={user};
                pwd={password};
                Database=X;''')

            # Return both connection and cursor objects as a tuple
            print("Connected to Database connect function")
            return conn, conn.cursor()

        except Exception as e:
            print("Error:", e)
        return None, None

    def disconnect(self, conn):
        if conn:
            conn.close()

    def check_for_masterdata(self, name):
        conn, cursor = self.connect()
        try:
            #name = name[:13]
            # query = 'SELECT WCSTSTDB.HLARTIP.ARCART FROM WCSTSTDB.HLARTIP WHERE WCSTSTDB.HLARTIP.ARCART = ?'
            query = 'SELECT WCSTSTDB.HLARTIP.ARCART FROM WCSTSTDB.HLARTIP INNER JOIN WCSTSTDB.HLVLIDP ON ARCART = VICART WHERE WCSTSTDB.HLVLIDP.VICIVL = ?'
            cursor.execute(query, (name,))
            result = cursor.fetchone()
            if result:
                return result[0]  # Returning the maximum quantity
            else:
                return None  # Returning None if item not found
        finally:
            self.disconnect(conn)

    def check_for_masterdata_guess(self, sku):
        conn, cursor = self.connect()
        try:
            #name = name[:13]
            # query = 'SELECT WCSTST_DAT.GNERM3P.E3NUPC FROM WCSTST_DAT.GNERM3P WHERE WCSTST_DAT.GNERM3P.E3NUPC = ?'
            query = 'SELECT WCSTST_DAT.GNERM3P.E3NUPC FROM WCSTSTDB.HLVLIDP lvid JOIN WCSTSTDB.HLVLIDP upc ON lvid.VICART=upc.VICART AND upc.VICTYI<>lvid.VICTYI JOIN WCSTST_DAT.GNERM3P ON trim(upc.vicivl)=trim(E3NUPC) OR trim(lvid.vicivl)=trim(E3NUPC) WHERE lvid.VICIVL = ?'
            cursor.execute(query, (sku,))
            result = cursor.fetchone()
            if result:
                self.sku = result[0]
                return result[0]  # Returning the maximum quantity
            else:
                return None  # Returning None if item not found
        finally:
            self.disconnect(conn)

    def get_pick_id(self, sku):
        conn, cursor = self.connect()
        if cursor is None:  # Check if connection failed
            return None
        try:
            # Prepare the query, correctly parameterized and without syntax errors
            # query = '''
            #             SELECT WCSTST_DAT.GNERM3P.E3PONB, WCSTST_DAT.GNERM3P.E3NUPC, SUM(WCSTST_DAT.GNERM3P.E3QQTY) QTY ,substr(ARMDAR, 1, 6)||' '||substr(ARMDAR, 7, 5)||' '||substr(ARMDAR, 12, 5) ModParCol, D.VCVAIC AS Size
            #             FROM WCSTST_DAT.GNERM3P
            #             inner JOIN wcststdb.HLARTIP ON ARCART=WCSTST_DAT.GNERM3P.E3NUPC
            #             inner join wcststdb.HLVAICL1 D on  ARNOBJ = D.VCNOBJ and D.VCCICM = 'COD_TAGLIA'
            #             WHERE WCSTST_DAT.GNERM3P.E3PONB = ?
            #             GROUP BY WCSTST_DAT.GNERM3P.E3PONB, WCSTST_DAT.GNERM3P.E3NUPC, substr(ARMDAR, 1, 6)||' '||substr(ARMDAR, 7, 5)||' '||substr(ARMDAR, 12, 5), D.VCVAIC

            #             '''
            query = '''
                WITH ID AS (SELECT upc.vicivl UPC, lvid.vicivl EAN, substr(ARMDAR, 1, 6)||' '||substr(ARMDAR, 7, 5)||' '||substr(ARMDAR, 12, 5) ModParCol, D.VCVAIC Size
 	            FROM WCSTSTDB.HLVLIDP lvid
 		        LEFT JOIN WCSTSTDB.HLVLIDP upc ON lvid.VICART=upc.VICART AND upc.VICTYI<>lvid.VICTYI
 		        INNER JOIN wcststdb.HLARTIP ON (upc.vicivl)=(arcart) OR (lvid.vicivl)=(arcart)
 		        inner join wcststdb.HLVAICL1 D on  ARNOBJ = D.VCNOBJ and D.VCCICM = 'COD_TAGLIA'
 	            WHERE lvid.VICIVL IN (SELECT WCSTST_DAT.GNERM3P.E3NUPC FROM WCSTST_DAT.GNERM3P WHERE WCSTST_DAT.GNERM3P.E3PONB = ?)
                )
                SELECT WCSTST_DAT.GNERM3P.E3PONB, WCSTST_DAT.GNERM3P.E3NUPC, WCSTST_DAT.GNERM3P.E3QQTY QTY ,ID.ModParCol ModParCol, ID.SIZE Size
	            FROM WCSTST_DAT.GNERM3P
		        inner JOIN ID ON ID.UPC=WCSTST_DAT.GNERM3P.E3NUPC OR ID.EAN = WCSTST_DAT.GNERM3P.E3NUPC and WCSTST_DAT.GNERM3P.E3PONB= ?
                    '''
            
            cursor.execute(query, (sku, sku))
            results = cursor.fetchall()  # Consider using fetchall if expecting multiple rows
            return results  # Return the full result set
        finally:
            self.disconnect(conn)

    def get_max_quantity(self, name, pid):
        conn, cursor = self.connect()
        try:
            # Trim the input data to fit within the maximum allowed length
            #name = name[:13]  # Adjust max_allowed_length as per your database schema
            print(f'pid: {pid}')
            print(f'name: {name}')
            # query = 'SELECT SUM(WCSTST_DAT.GNERM3P.E3QQTY) FROM WCSTST_DAT.GNERM3P WHERE WCSTST_DAT.GNERM3P.E3NUPC = ? AND WCSTST_DAT.GNERM3P.E3PONB = ?'
            query = '''
                    SELECT SUM(WCSTST_DAT.GNERM3P.E3QQTY)
                    FROM WCSTSTDB.HLVLIDP lvid
                    LEFT JOIN WCSTSTDB.HLVLIDP upc 
                        ON lvid.VICART=upc.VICART AND upc.VICTYI<>lvid.VICTYI
                    INNER JOIN WCSTST_DAT.GNERM3P 
                        ON (trim(upc.vicivl)=trim(E3NUPC) OR trim(lvid.vicivl)=trim(E3NUPC)) AND WCSTST_DAT.GNERM3P.E3PONB = ?
                    WHERE lvid.VICIVL = ?
                    '''
            cursor.execute(query, (pid, name))
            result = cursor.fetchone()
            if result:
                print(f'Called MAXQTY {result[0]}')
                return result[0]  # Returning the maximum quantity
            else:
                return None  # Returning None if item not found
        finally:
            self.disconnect(conn)

    def get_max_quantity_sku(self, name):
        conn, cursor = self.connect()
        try:
            # Trim the input data to fit within the maximum allowed length
            #name = name[:13]  # Adjust max_allowed_length as per your database schema
            print(f'name: {name}')
            # query = 'SELECT SUM(WCSTST_DAT.GNERM3P.E3QQTY) FROM WCSTST_DAT.GNERM3P WHERE WCSTST_DAT.GNERM3P.E3NUPC = ?'
            query = '''
                    SELECT SUM(WCSTST_DAT.GNERM3P.E3QQTY)
                    FROM WCSTSTDB.HLVLIDP lvid
                    LEFT JOIN WCSTSTDB.HLVLIDP upc 
                        ON lvid.VICART=upc.VICART AND upc.VICTYI<>lvid.VICTYI
                    INNER JOIN WCSTST_DAT.GNERM3P 
                        ON (trim(upc.vicivl)=trim(E3NUPC) OR trim(lvid.vicivl)=trim(E3NUPC)) 
                    WHERE lvid.VICIVL = ?
                    '''
            cursor.execute(query, (name,))
            result = cursor.fetchone()
            if result:
                print(f'Called MAXQTY {result[0]}')
                return result[0]  # Returning the maximum quantity
            else:
                return None  # Returning None if item not found
        finally:
            self.disconnect(conn)

    def check_receiving_data(self, pickid, sku):
        conn, cursor = self.connect()
        try:
            max_length_sku = 13
            max_length_pickid = 8
            # Truncate the data to match database field sizes
            sku = sku[:max_length_sku]  # Adjust 'max_length_sku' to the max length of the sku column
            pickid = pickid[:max_length_pickid]  # Adjust 'max_length_pickid' to the max length of the PICKID column

            # query = 'SELECT SUM(R710KZDA.RECEIVING.QTY) FROM R710KZDA.RECEIVING WHERE R710KZDA.RECEIVING.SKU = ? AND R710KZDA.RECEIVING.PICKID = ?'
            query = '''SELECT SUM(R710KZDA.RECEIVING.QTY)
                        FROM WCSTSTDB.HLVLIDP lvid
                        LEFT JOIN WCSTSTDB.HLVLIDP upc 
                            ON lvid.VICART=upc.VICART AND upc.VICTYI<>lvid.VICTYI
                        INNER JOIN R710KZDA.RECEIVING 
                            ON (trim(upc.vicivl)=trim(SKU) OR trim(lvid.vicivl)=trim(SKU)) AND R710KZDA.RECEIVING.PICKID = ?
                        WHERE lvid.VICIVL = ?'''
            cursor.execute(query, (pickid, sku))
            result = cursor.fetchone()
            if result:
                return result[0]  # Returning the sum of quantities
            else:
                return 0  # Returning 0 if no result found
        except Exception as e:
            print(f"Error checking receiving data: {e}")
        finally:
            self.disconnect(conn)

    # def insert_error_data(self, pid=None, sku=None, message='INSERT ERROR DATA!'):
    #     # Establish a connection
    #     conn, cursor = self.connect()
        
    #     try:
    #         # Define the SQL query
    #         query = 'INSERT INTO R710KZDA.ERRORS (ctime, sku, qty, cuser, pickid, comments) VALUES (CURRENT TIMESTAMP, ?, 1, ?, ?, ?)'
            
    #         # Strip values of any leading or trailing whitespace
    #         pid = pid.strip() if pid is not None else None
    #         sku = sku.strip() if sku is not None else None
    #         message = message.strip()  # Always strip the message
            
    #         # Check if sku exceeds the maximum allowed size
    #         max_sku_length = 13  # Maximum length defined in the database schema
    #         if sku and len(sku) > max_sku_length:
    #             print(f"Warning: SKU '{sku}' exceeds the maximum allowed size of {max_sku_length} characters. Truncating...")
    #             sku = sku[:max_sku_length]  # Truncate the sku value
            
    #         # Execute the SQL query
    #         cursor.execute(query, (sku, self.username, pid, message))
    #         conn.commit()
    #         print('Entry does not exist, saved into Error Database.')
    #     except Exception as e:
    #         print(f"Error inserting error data: {e}")
    #     finally:
    #         # Always ensure the connection is closed, even if an error occurs
    #         self.disconnect(conn)

    def insert_error_data(self, pid='', sku='', message='INSERT ERROR DATA!'):
        # Establish a connection
        conn, cursor = self.connect()
        
        try:
            # Check if the record already exists
            cursor.execute("SELECT COUNT(*) FROM R710KZDA.ERRORS WHERE sku = ? AND cuser = ? AND pickid = ? AND comments = ?", (sku, self.username, pid, message))
            existing_records_count = cursor.fetchone()[0]
            
            if existing_records_count > 0:
                #logging.warning(f"Record already exists. SKU: '{sku}', PID: '{pid}', Message: '{message}'")
                return

            # Define the SQL query to insert the record
            query = '''
                INSERT INTO R710KZDA.ERRORS (ctime, sku, qty, cuser, pickid, comments)
                VALUES (CURRENT TIMESTAMP, ?, 1, ?, ?, ?)
            '''

            # Execute the SQL query
            cursor.execute(query, (sku, self.username, pid, message))
            conn.commit()
            return f"Entry inserted. SKU: '{sku}', PID: '{pid}', Message: '{message} into Error Database"
          
        except Exception as e:
            # logging.error(f"Error inserting error data: {e}. SKU: '{sku}', PID: '{pid}', Message: '{message}'. Query: {query}")
            print(f"Error inserting error data: {e}")
        finally:
            # Always ensure the connection is closed, even if an error occurs
            self.disconnect(conn) 

    def SKU_convertor(self, sku):
        sku = sku.strip()
        if len(sku) == 12:
            conn, cursor = self.connect() 
            try:
                query = '''
                        SELECT WCSTST_DAT.GNERM3P.E3NUPC 
                        FROM WCSTSTDB.HLVLIDP lvid 
                        JOIN WCSTSTDB.HLVLIDP upc ON lvid.VICART=upc.VICART AND upc.VICTYI<>lvid.VICTYI 
                        JOIN WCSTST_DAT.GNERM3P ON TRIM(upc.vicivl)=TRIM(E3NUPC) OR TRIM(lvid.vicivl)=TRIM(E3NUPC) 
                        WHERE TRIM(lvid.VICIVL) = ?
                        '''
                cursor.execute(query, (sku,))
                result = cursor.fetchone()
                if result is None:
                    print('SKU does not exist')
                    # You can choose to raise an exception here if needed.
                    # raise ValueError('SKU does not exist')
                else:
                    new_sku = result[0]  # Retrieve the new SKU from the database
                    print(f'Retrieved SKU: {new_sku}')
                    return new_sku  # Return the new SKU
            except pyodbc.Error as e:
                print(f'Database error: {e}')
                # You may want to log the error or handle it differently.
            except Exception as ex:
                print(f'Error occurred: {ex}')
                # Handle any other unexpected exceptions.
            finally:
                self.disconnect(conn)
        else: 
            print(f'Invalid SKU length: {sku}')
            return sku  # Return the original SKU if it's not 12 characters long
  
    def insert_receiving_data_sku(self, sku, pid=None, qty=1):
        sku = self.SKU_convertor(sku)  # Stripping SKU input
        
        try:
            conn, cursor = self.connect()
            query = '''INSERT INTO R710KZDA.RECEIVING (sku, qty, cuser, pickid) VALUES (CURRENT TIMESTAMP, ?, ?, ?, ?)'''
            cursor.execute(query, (sku, qty, self.username.strip(), pid.strip()))  # Stripping username and pid inputs
            conn.commit()

            print(f"Inserted data: ctime={self.ctime}, sku={sku}, qty={qty}, cuser={self.username}, pickid = {pid}")
        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            self.disconnect(conn)

    def insert_receiving_data(self, pid, sku, qty, modelpart, line, category):
        sku = self.SKU_convertor(sku)  # Stripping SKU input
        print(f'After converting SCU:{sku}')
        try:
            conn, cursor = self.connect()

            # Convert to appropriate data types as needed
    
            qty_int = int(qty)
            cuser = self.username.strip()  # Stripping username input
            sku = sku.strip()
            print(f"Prepared to insert: sku={sku}, qty={qty_int}, cuser={cuser}, pickid={pid.strip()}, modelpart={modelpart.strip()}, line={line.strip()}, category={category.strip()}")

            # Updated SQL query to use CURRENT TIMESTAMP for the current time and correct column names
            query = '''
            INSERT INTO R710KZDA.RECEIVING (ctime, sku, qty, cuser, pickid, modelpart, line, category)
            VALUES (CURRENT TIMESTAMP, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (sku, qty_int, cuser, pid.strip(), modelpart.strip(), line.strip(), category.strip()))  # Stripping all input strings
            conn.commit()

            # Now insert into R710KZDA.LABEL.PICKID with a condition to ensure uniqueness
#             query_missing_label = '''
#             INSERT INTO R710KZDA.LABELS.PICKID (PICKID)
#             SELECT ?
#             WHERE NOT EXISTS (
#                 SELECT 1
#                 FROM R710KZDA.LABELS.PICKID
#                 WHERE PICKID = ?
# )
#             '''
#             cursor.execute(query_missing_label, (pid.strip()), pid.strip())  # Stripping pid input
#             conn.commit()

#             print("Successfully inserted data.")
#             print("Successfully inserted data into R710KZDA.LABEL.PICKID.")
        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            self.disconnect(conn)

    def insert_pick_error_data_pickid(self, pickid, message=None):
        conn, cursor = self.connect()
        try:
            pickid = pickid.strip()

            if message:
                message = message.strip()

            query_check_existing = f'''SELECT 1
                                        FROM R710KZDA.ERRORS
                                        WHERE sku = '' AND cuser = '{self.username}' AND pickid = '{pickid}' AND comments = '{message}'
                                        FETCH FIRST 1 ROWS ONLY'''

            cursor.execute(query_check_existing)
            existing_record = cursor.fetchone()

            if not existing_record:  # Insert only if no existing record found
                query_insert = f'''INSERT INTO R710KZDA.ERRORS (ctime, sku, qty, cuser, pickid, comments)
                                    VALUES (CURRENT TIMESTAMP, '', 1, '{self.username}', '{pickid}', '{message}')'''
                cursor.execute(query_insert)
                conn.commit()
                self.disconnect(conn)
                return "Error data inserted successfully."
            else:
                self.disconnect(conn)
                return "Error data already exists."

        except pyodbc.Error as pyodbc_error:
            error_message = f"PyODBC Error: {pyodbc_error}"
            conn.rollback()  # Rollback in case of error
            self.disconnect(conn)
            return f"Error inserting error data: {pyodbc_error}"
        except Exception as e:
            error_message = f"Error inserting error data: {e}"
            conn.rollback()  # Rollback in case of error
            self.disconnect(conn)
            return error_message



    def check_sku_for_PID(self, sku, pickid):
        conn,cursor = self.connect()
        if cursor is None:
            return None
        try:

            query = '''WITH ID AS (SELECT upc.vicivl UPC, lvid.vicivl EAN, lvid.VICart SKU
                                FROM WCSTSTDB.HLVLIDP lvid
                                LEFT JOIN WCSTSTDB.HLVLIDP upc ON lvid.VICART=upc.VICART AND upc.VICTYI<>lvid.VICTYI WHERE lvid.VICIVL = ?)                        
                    SELECT E3PONB AS sku 
                    FROM WCSTST_DAT.GNERM3P
                    inner JOIN ID ON ID.UPC=WCSTST_DAT.GNERM3P.E3NUPC OR ID.EAN = WCSTST_DAT.GNERM3P.E3NUPC and WCSTST_DAT.GNERM3P.E3PONB= ? '''
            cursor.execute(query, (sku, pickid))
            results = cursor.fetchall() 
             # Consider using fetchall if expecting multiple rows
            if results is None:
                print(results)
                return None
            else:
                return results  # Return the full result set
        finally:
            self.disconnect(conn)

    def get_sku(self, ponb):
        conn, cursor = self.connect()
        if cursor is None:  # Check if connection failed
            return None
        try:
            # Prepare the query, correctly parameterized and without syntax errors
            query = '''
                        SELECT WCSTST_DAT.GNERM3P.E3PONB, WCSTST_DAT.GNERM3P.E3NUPC, SUM(WCSTST_DAT.GNERM3P.E3QQTY) 
                        FROM WCSTST_DAT.GNERM3P 
                        WHERE WCSTST_DAT.GNERM3P.E3NUPC = ? 
                        GROUP BY WCSTST_DAT.GNERM3P.E3PONB, WCSTST_DAT.GNERM3P.E3NUPC
                        '''
            cursor.execute(query, (ponb,))

            results = cursor.fetchall()
            conn.close()
             # Consider using fetchall if expecting multiple rows
            if results is None:
                print(results)
                return None
            else:
                conn.close()
                return results
              # Return the full result set
        finally:
            self.disconnect(conn)

    def get_model_link_line_category(self, pid):
        """Retrieve model information, including an image link, for a given sku."""
        conn, cursor = self.connect()

        if cursor is None:  # Check if the connection failed
            print("Failed to establish a database connection.")
            return None
        try:

            query = '''
                WITH ProductGroup as(SELECT FACFAR, FALFAR, COTXTC 
                                        FROM wcststdb.HLFARTL1 
                                        LEFT JOIN wcststdb.HLCOMMP ON CONCOM=FANCOM AND COCFCO = 'RET'
                                        WHERE FACFAN = 'LINE' AND FATFBA = '1' ),
                    ID AS (SELECT upc.vicivl UPC, lvid.vicivl EAN, lvid.VICart SKU
                            FROM WCSTSTDB.HLVLIDP lvid
                            LEFT JOIN WCSTSTDB.HLVLIDP upc ON lvid.VICART=upc.VICART AND upc.VICTYI<>lvid.VICTYI WHERE lvid.VICIVL = ?)
                                    SELECT AICART SKU,  
                                    SUBSTR(AICODI, 1, 6)||SUBSTR(AICODI, 13, 5) MODELPART, 
                                    'https://X'||SUBSTR(AICODI, 1, 6)||SUBSTR(AICODI, 13, 5)||'-'||SUBSTR(AICODI, 18, 5) link, 
                                    X.A2CFAR as Line, 
                                    ProductGroup.COTXTC Category FROM wcstst_dat.gnarcap
                                        INNER JOIN ID ON ID.SKU=AICART
                                        inner join wcststdb.hlcdfap X on  AICART = X.A2cart and X.A2CFAN = 'LINE' 
                                        INNER JOIN ProductGroup ON ProductGroup.FACFAR = X.A2CFAR
                    '''
            cursor.execute(query, (pid,))
            results = cursor.fetchone()
          
            if not results:
                print("No data found for PID:", pid)
                return None
            return results
        except Exception as e:
            print(f"Error executing query: {e}")
        finally:
            cursor.close()
            self.disconnect(conn)

    def insert_or_update_label(self, pid):
        conn, cursor = self.connect()
        try:
            # Strip whitespace from the input PICKID
            pid = pid.strip()
            if len(pid) > 8:
                return "Error: PICKID exceeds maximum length of 8 characters."
            
            # Check if the entry exists
            cursor.execute("SELECT COUNT(*) FROM R710KZDA.LABELS WHERE PICKID = ?", (pid,))
            if cursor.fetchone()[0] == 0:
                # If it does not exist, insert new entry with QTY set to 1
                cursor.execute("INSERT INTO R710KZDA.LABELS (CTIME, PICKID, MISSINGLABELS) VALUES (CURRENT TIMESTAMP, ?, 1)", (pid,))
            else:
                # If it exists, update the QTY by incrementing it
                cursor.execute("UPDATE R710KZDA.LABELS SET MISSINGLABELS = MISSINGLABELS + 1 WHERE PICKID = ?", (pid,))
            conn.commit()
        except Exception as e:
            print(f'Error occurred: {e}')  # More detailed error logging
            return f'Error occurred: {e}'
        finally:
            self.disconnect(conn)
