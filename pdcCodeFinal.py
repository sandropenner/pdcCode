import os
import re
import time
import xml.etree.ElementTree as ET
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

name_patterns = [
    re.compile(r'(<Name>).*?W_(.*?</Name>)'),
    re.compile(r'(<Name>).*?C_(.*?</Name>)'),
    re.compile(r'(<Name>).*?S_(.*?</Name>)'),
    re.compile(r'(<Name>).*?HSS_(.*?</Name>)'),
    re.compile(r'(<Name>).*?L_(.*?</Name>)'),
    re.compile(r'(<Name>).*?HP_(.*?</Name>)'),]
remnant_location_pattern = re.compile(r'<RemnantLocation>.*?</RemnantLocation>', re.DOTALL)
tag_patterns = [re.compile(fr'(<{tag}>)(.{{25,}})(</{tag}>)') for tag in ['Filename', 'DrawingIdentification', 'PieceIdentification']]

def remove_SI_block(filepath):
    try:
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
    except Exception as e:
        pass

def transform_id(value):
    parts = value.split('-')
    if len(parts) != 3:
        return value
    first_char_last, remaining_last = parts[2][0], parts[2][1:]
    if remaining_last.isdigit():
        parts[2] = first_char_last + remaining_last.lstrip('0')
    if parts[1].isdigit():
        parts[1] = parts[1].lstrip('0')
    elif any(char.isdigit() for char in parts[1]): 
        alpha_part = ''.join(filter(str.isalpha, parts[1]))
        num_part = ''.join(filter(str.isdigit, parts[1]))
        parts[1] = alpha_part + num_part.lstrip('0')
    transformed_value = '-'.join(parts)
    return transformed_value

def process_idstv_file_BL(idstv_file):
    try:
        with open(idstv_file, 'r') as file:
            content = file.read()
        for pattern in name_patterns:
            content = pattern.sub(r'\1\2', content)
        content = remnant_location_pattern.sub('<RemnantLocation>v</RemnantLocation>', content)
        for pattern in tag_patterns:
            content = pattern.sub(lambda m: m.group(1) + m.group(2)[10:] + m.group(3), content)
        with open(idstv_file, 'w') as file:
            file.write(content)
    except PermissionError:
        time.sleep(1)
        process_idstv_file_BL(idstv_file)
    except Exception as e:
        pass

def process_idstv_file_AM(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        for ba in root.findall('.//BA'):
            profile_type = ba.find('ProfileType')
            if profile_type is not None and profile_type.text == 'L':
                for pi in root.findall(".//PI"):
                    length_element = pi.find("Length")
                    if length_element is not None and float(length_element.text) < 279:
                        for tag in ['Filename', 'DrawingIdentification', 'PieceIdentification']:
                            tag_element = pi.find(tag)
                            if tag_element is not None:
                                tag_element.text = transform_id(tag_element.text)
                tree.write(filepath, xml_declaration=True, encoding="UTF-8")
    except ET.ParseError as e:
        pass

def process_nc1_files_BL(file_path):
    try:
        if file_path.endswith(".nc1"):
            filename = os.path.basename(file_path)
            directory = os.path.dirname(file_path)
            if len(filename) >= 25:
                new_file_path = os.path.join(directory, filename[10:])
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                if len(lines) >= 5:
                    for i in range(3, 5):
                        if len(lines[i].strip()) >= 25:
                            lines[i] = lines[i][12:]
                with open(new_file_path, 'w') as file:
                    file.writelines(lines)
                if new_file_path != file_path:
                    os.remove(file_path)
    except Exception as e:
        pass

class CombinedHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith(".nc1"):
            remove_SI_block(event.src_path)
            process_nc1_files_BL(event.src_path)
        elif event.src_path.endswith(".idstv"):
            process_idstv_file_BL(event.src_path)
            process_idstv_file_AM(event.src_path)

def main():
    event_handler = CombinedHandler()
    observer = Observer()
    directories_file_path = 'folders_settings.txt'
    try:
        with open(directories_file_path, 'r') as file:
            folders_to_track = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        pass
        return
    for folder in folders_to_track:
        if os.path.exists(folder):
            observer.schedule(event_handler, folder, recursive=True)
        else:
            pass
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
