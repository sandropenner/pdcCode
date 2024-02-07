import os
import xml.etree.ElementTree as ET
import shutil  # Import the shutil module at the beginning of your file
def transform_id(value):
    parts = value.split('-')
    if len(parts) != 3:
        return value  # Return the original value if it doesn't have three parts separated by dashes

    # Remove all zeros between the first and last dash
    #parts[1] = parts[1].replace('0', '')
    
    # Remove zeros after the last dash and after the first character up to the next character
    first_char = parts[2][0]  # Get the first character
    remaining = parts[2][1:]  # Get the remaining part
    remaining = remaining.lstrip('0')  # Remove leading zeros
    parts[2] = first_char + remaining  # Combine them back
    return ''.join(parts)  # Remove the dashes

def process_idstv_file(filepath):
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

def process_nc1_files(directory):
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

def main():
    directory = input("Please enter the directory containing .idstv and .nc1 files: ")

    idstv_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".idstv")]

    if not idstv_files:
        print("No .idstv files found in the specified directory.")
        return

    for filepath in idstv_files:
        process_idstv_file(filepath)

    process_nc1_files(directory)

if __name__ == "__main__":
    main()
