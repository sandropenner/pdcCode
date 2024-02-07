import os
import re
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to remove the SI block from .nc1 files
def remove_SI_block(filepath):
    try:
        with open(filepath, 'r') as file:
            lines = file.readlines()
        new_lines = [line for line in lines if not line.strip().startswith("SI")]
        with open(filepath, 'w') as file:
            file.writelines(new_lines)
        logging.info(f"SI block removed from {filepath}")
    except Exception as e:
        logging.error(f"Error removing SI block from {filepath}: {e}")

# Function to transform ID
def transform_id(value):
    parts = value.split('-')
    if len(parts) != 3:
        return value
    first_char, remaining = parts[2][0], parts[2][1:].lstrip('0') if parts[2][1:].isdigit() else parts[2][1:]
    parts[2] = first_char + remaining
    return ''.join(parts)

# Function to process .idstv file
def process_idstv_file(idstv_file):
    try:
        with open(idstv_file, 'r') as file:
            content = file.read()
        # Process content with regular expressions
        content = re.sub(r'(<Name>).*?W_(.*?</Name>)', r'\1\2', content)
        content = re.sub(r'(<Name>).*?C_(.*?</Name>)', r'\1\2', content)
        content = re.sub(r'(<Name>).*?S_(.*?</Name>)', r'\1\2', content)
        content = re.sub(r'(<Name>).*?HSS_(.*?</Name>)', r'\1\2', content)
        content = re.sub(r'(<Name>).*?L_(.*?</Name>)', r'\1\2', content)
        content = re.sub(r'(<Name>).*?HP_(.*?</Name>)', r'\1\2', content)
        content = re.sub(r'<RemnantLocation>.*?</RemnantLocation>', '<RemnantLocation>v</RemnantLocation>', content)
        # Trim the first 10 characters for the specified tags only if content is 25+ characters long
        for tag in ['Filename', 'DrawingIdentification', 'PieceIdentification']:
            pattern = fr'(<{tag}>)(.{{25,}})(</{tag}>)'
            content = re.sub(pattern, lambda m: m.group(1) + m.group(2)[10:] + m.group(3), content)
        with open(idstv_file, 'w') as file:
            file.write(content)
        logging.info(f"Processed {idstv_file}")
    except Exception as e:
        logging.error(f"Error processing {idstv_file}: {e}")

# Function to process .nc1 files
def process_nc1_file(file_path):
    if not os.path.exists(file_path) or not file_path.endswith(".nc1"):
        return
    try:
        filename = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        if file_path.endswith(".nc1") and len(filename) >= 25:
            new_file_path = os.path.join(directory, filename[10:])
            with open(file_path, "r") as file_obj:
                lines = file_obj.readlines()
            if len(lines) >= 5: 
                for i in [3, 4]: 
                    if len(lines[i].strip()) >= 25:
                        lines[i] = lines[i][12:]
            with open(file_path, "w") as file_obj:
                file_obj.writelines(lines)
            os.rename(file_path, new_file_path)
        logging.info(f"Processed {file_path}")
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")

# Custom FileSystemEventHandler
class CustomEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            if event.src_path.endswith(".nc1"):
                remove_SI_block(event.src_path)
                process_nc1_file(event.src_path)
            elif event.src_path.endswith(".idstv"):
                process_idstv_file(event.src_path)
            logging.info(f"Handled {event.src_path}")

if __name__ == "__main__":
    path_to_watch = "path/to/directory" # Update this path as needed
    event_handler = CustomEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=True)
    observer.start()
    logging.info(f"Started monitoring {path_to_watch}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
