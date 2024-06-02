import threading
import re
import os
import keyboard 

class ScannerWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.buffer = ""
        self.running = False
        self.paused = False

        self.on_scan_callback = None

    def extract_numbers(self, input_str):
        if input_str.isnumeric() and ((len(input_str) == 13 or len(input_str) == 12) or len(input_str) == 8):
            code_type = 'SKU' if (len(input_str) ==12 or len(input_str) == 13) else 'PID'
            return input_str, code_type
        
        elif input_str.isnumeric() and len(input_str) == 2:
            code_type  = 'ORDER66'
            return input_str, code_type
        else:
            return None, 'Unknown'

    def on_key_event(self, event):
        if not self.running or self.paused:
            return  # Ignore events if not running
        if event.event_type == keyboard.KEY_UP:
            if event.name == 'enter':
                raw_code = self.buffer.strip()
                raw_code = ''.join(re.findall('[0-9]', raw_code))
                code, code_type = self.extract_numbers(raw_code)
                if code:
                    if self.on_scan_callback:
                        self.on_scan_callback(code, code_type)
                else:
                    print("Invalid input, code does not meet criteria.")
                    self.on_scan_callback(code, code_type)
                self.buffer = ""  # Reset buffer after processing
            else:
                self.buffer += event.name if event.name.isprintable() else ''

    def run(self):
        self.running = True
        keyboard.hook(self.on_key_event)

    def stop(self):
        self.running = False
        os._exit(1)

    def set_on_scan_callback(self, callback):
        self.on_scan_callback = callback

    def pause(self):
        self.paused = not self.paused  # Toggle the pause state
