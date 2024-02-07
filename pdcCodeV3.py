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

#  process_idstv_file function is used to process the .idstv file, thus removing unwanted information from the .idstv file
def process_idstv_file_BL(idstv_file):
    while True:
        try:
            with open(idstv_file, 'r') as file:
                content = file.read()
# Existing processing
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
            break  
        except PermissionError:
            print(f"Waiting for file {idstv_file} to be released")
            time.sleep(1)

# Function to check for 'L' in the specified location in .idstv files
def process_idstv_file_AM(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        for ba in root.findall('.//BA'):
            profile_type = ba.find('ProfileType')
            if profile_type is not None and profile_type.text == 'L':
                try:
                    tree = ET.parse(filepath)
                    root = tree.getroot()
                    for pi in root.findall(".//PI"):
                        length_element = pi.find("Length")
                        if length_element is not None:
                            length = float(length_element.text)
                            if length < 279:
                                print(f"Found a Length of {length} which is less than 279 for file {filepath}.")
                                for tag in ['Filename', 'DrawingIdentification', 'PieceIdentification']:
                                    tag_element = pi.find(tag)
                                    if tag_element is not None:
                                        tag_element.text = transform_id(tag_element.text)
                    tree.write(filepath, xml_declaration=True, encoding="UTF-8")
                    print(f"{filepath} has been processed.")
                except (FileNotFoundError, ET.ParseError) as e:
                    print(f"Error processing file {filepath}. Error: {e}")
                    return False
    except ET.ParseError:
        print(f"XML parsing error in file {filepath}.")
        return False

# check if the file is .nc1 and if the length of the filename is greater than 25 characters and Modify lines 4 and 5 
def process_nc1_files_BL(file_path):
    if not os.path.exists(file_path):
        return
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
        print(f"{filename} has been modified and saved as {filename[10:]}.")

# Function to check for 'L' in the specified location in .idstv files
def process_nc1_files_AM(directory):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        for ba in root.findall('.//BA'):
            profile_type = ba.find('ProfileType')
            if profile_type is not None and profile_type.text == 'L':
                try:
                    nc1_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".nc1")]
                    for filepath in nc1_files:
                        with open(filepath, 'r') as file:
                            lines = file.readlines()
                        if len(lines) > 10:
                            try:
                                length_value = float(lines[10].strip())
                            except ValueError:
                                continue  # Skip the file if the length_value is not a number
                            if length_value < 279:
                                for i in [3, 4]:
                                    lines[i] = transform_id(lines[i].strip()) + '\n'
                                with open(filepath, 'w') as file:
                                    file.writelines(lines)
                                new_filename = transform_id(lines[3].strip())
                                new_filepath = os.path.join(directory, new_filename + ".nc1")
                                shutil.move(filepath, new_filepath)
                                print(f"File {filepath} renamed to {new_filepath}")
                except (FileNotFoundError, ET.ParseError) as e:
                    print(f"Error processing file {filepath}. Error: {e}")
                    return False
    except ET.ParseError:
        print(f"XML parsing error in file {filepath}.")
        return False

class CombinedHandler(FileSystemEventHandler):
    def on_created(self, event):
        print(f'event type: {event.event_type}  path: {event.src_path}')
        file = event.src_path
        if file.endswith(".nc1"):
            remove_SI_block(file)
            process_nc1_files_BL
            process_nc1_files_AM
        elif file.endswith(".idstv"):
            process_idstv_file_BL
            process_idstv_file_AM
            
# calls the program to watch the txt list of dirs
if __name__ == "__main__":
    event_handler = CombinedHandler()
    observer = Observer()
    directories_file_path = 'folders_settings.txt'
    with open(directories_file_path, 'r') as file:
        folders_to_track = [line.strip() for line in file if line.strip()]

    for folder in folders_to_track:
        if not os.path.exists(folder):
            print(f"ERROR: Cannot access path {folder}")
            continue
        observer.schedule(event_handler, folder, recursive=True)

    observer.start()
    print(f"Monitoring started on folders: {', '.join(folders_to_track)}...")

    while True:
        time.sleep(1)
