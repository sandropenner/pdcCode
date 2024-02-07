import os
import re
import time
import shutil
import xml.etree.ElementTree as ET
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Function to remove the SI block from .nc1 files
def remove_SI_block(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()
    new_lines = []
    skip = False
    for line in lines:
        if line.strip().startswith("SI"):
            skip = True
        elif len(line.strip()) == 2 and not line.strip().startswith('  '):
            skip = False
        if not skip:
            new_lines.append(line)
    with open(filepath, 'w') as file:
        file.writelines(new_lines)

# Transform ID function used in process_idstv_file
def transform_id(value):
    parts = value.split('-')
    if len(parts) != 3:
        return value
    first_char = parts[2][0]
    if parts[2][1:].isdigit():
        remaining = parts[2][1:].lstrip('0')
        parts[2] = first_char + remaining
    else:
        pass
    return ''.join(parts)

# Function to process .idstv files with specific condition checks
def process_idstv_file(filepath):
    if check_idstv_condition(filepath):
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            for pi in root.findall(".//PI"):
                for tag in ['Filename', 'DrawingIdentification', 'PieceIdentification']:
                    tag_element = pi.find(tag)
                    if tag_element is not None:
                        tag_element.text = transform_id(tag_element.text)
            tree.write(filepath, xml_declaration=True, encoding="UTF-8")
            print(f"{filepath} has been processed.")
        except ET.ParseError as e:
            print(f"XML parsing error in file {filepath}: {e}")

# Function to check for 'L' in the specified location in .idstv files
def check_idstv_condition(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        for ba in root.findall('.//BA'):
            profile_type = ba.find('ProfileType')
            if profile_type is not None and profile_type.text == 'L':
                return True
        return False
    except ET.ParseError:
        print(f"XML parsing error in file {filepath}.")
        return False

# Function to process and potentially rename .nc1 files
def process_and_rename_file(file_path):
    if file_path.endswith(".nc1") and check_nc1_condition(file_path):
        filename = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        new_file_path = os.path.join(directory, filename[10:])
        with open(file_path, "r") as file_obj:
            lines = file_obj.readlines()
        if len(lines) >= 5:
            for i in [3, 4]:
                if len(lines[i].strip()) >= 25:
                    lines[i] = "  " + transform_id(lines[i].strip()[12:]) + '\n'
        with open(new_file_path, "w") as file_obj:
            file_obj.writelines(lines)
        os.remove(file_path)  # Remove the original file after creating the new one
        print(f"{filename} has been processed and renamed.")

# Function to check for 'L' in line 10 of .nc1 files
def check_nc1_condition(filepath):
    try:
        with open(filepath, 'r') as file:
            lines = file.readlines()
        return 'L' in lines[9]
    except IndexError:
        return False
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return False

# Combined file event handler class
class CombinedHandler(FileSystemEventHandler):
    def on_created(self, event):
        print(f'Event type: {event.event_type}  path: {event.src_path}')
        file_path = event.src_path
        if file_path.endswith(".nc1"):
            remove_SI_block(file_path)
            process_and_rename_file(file_path)
        elif file_path.endswith(".idstv") and check_idstv_condition(file_path):
            process_idstv_file(file_path)

    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if file_path.endswith(".nc1"):
                process_and_rename_file(file_path)

if __name__ == "__main__":
    event_handler = CombinedHandler()
    observer = Observer()
    folders_to_track = [
        'N:\\Production\\PEDDINGHAUS IDSTV\\W8722', 
        'N:\\Production\\PEDDINGHAUS IDSTV\\W8733',
        'N:\\Production\\PEDDINGHAUS IDSTV\\W8747',
        'N:\\Production\\PEDDINGHAUS IDSTV\\W8745',
        'N:\\Production\\PEDDINGHAUS IDSTV\\W8749'
    ]
    for folder in folders_to_track:
        if not os.path.exists(folder):
            print(f"ERROR: Cannot access path {folder}")
            continue
        observer.schedule(event_handler, folder, recursive=True)
    observer.start()
    print(f"Monitoring started on folders: {', '.join(folders_to_track)}...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
