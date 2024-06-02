import keyboard
import threading
import re
import os


class ScannerWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.buffer = ""
        self.running = False
        self.on_scan_callback = None
        self.display_message_callback = None

    def extract_numbers(self, input_str):
        if input_str.isnumeric() and (len(input_str) == 13 or len(input_str) == 18):
            code_type = 'SCU' if len(input_str) == 13 else 'HD'
            return input_str, code_type
        
        elif input_str.isnumeric() and len(input_str) == 1:
            code_type = 'GRADE'
            return input_str, code_type
        
        elif input_str.isnumeric() and len(input_str) == 8:
            code_type = 'PID'
            return input_str, code_type
        else:
            return None, 'Unknown'

    def on_key_event(self, event):
        if not self.running:
            return  # Ignore events if not running
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'enter':
                raw_code = self.buffer.strip()
                raw_code = ''.join(re.findall('[0-9]', raw_code))
                code, code_type = self.extract_numbers(raw_code)
                if code:
                    if self.on_scan_callback:
                        self.on_scan_callback(code, code_type)
                else:
                    if self.display_message_callback:  # Check if callback is set
                        self.display_message_callback("Invalid input, code does not meet criteria.", 'red')  # Use callback
                self.buffer = ""  # Reset buffer after processing
            else:
                self.buffer += event.name if event.name.isprintable() else ''

    def run(self):
        self.running = True
        keyboard.hook(self.on_key_event)
        #keyboard.wait('esc')  # Use 'esc' key to stop listening

    def stop(self):
        self.running = False
        os._exit(1)

    def handle_scan(code, code_type):
        print(f"Scanned Code: {code}, Code Type: {code_type}")
        return code, code_type

    def set_on_scan_callback(self, callback):
        self.on_scan_callback = callback

    def set_display_message_callback(self, callback):
        self.display_message_callback = callback