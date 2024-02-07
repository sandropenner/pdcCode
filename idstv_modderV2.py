import os

def replace_tag_content(file_content, tag, new_content):
    """Replace the content inside all occurrences of a specified tag."""
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    start_index = 0

    while True:
        found_start_index = file_content.find(start_tag, start_index)
        end_index = file_content.find(end_tag, found_start_index)

        if found_start_index == -1 or end_index == -1:
            break  # No more tags found, break the loop

        # Replace the tag content
        file_content = (
            file_content[:found_start_index + len(start_tag)] 
            + new_content 
            + file_content[end_index:]
        )

        # Move past the last replaced tag
        start_index = found_start_index + len(start_tag) + len(new_content)

    return file_content

def process_idstv_files(directory, new_directory_path):
    try:
        idstv_files = [f for f in os.listdir(directory) if f.endswith('.idstv')]
    except Exception as e:
        print(f"Error accessing directory '{directory}': {e}")
        return

    print(f"Found {len(idstv_files)} .idstv files to process.")

    for idstv_file in idstv_files:
        idstv_file_path = os.path.join(directory, idstv_file)
        print(f"Processing file: {idstv_file}")

        try:
            with open(idstv_file_path, 'r') as file:
                file_content = file.read()
        except Exception as e:
            print(f"Error reading file '{idstv_file}': {e}")
            continue

        # Replace <Directory> content
        new_file_content = replace_tag_content(file_content, "Directory", new_directory_path)

        try:
            # Save the changes back to the file
            with open(idstv_file_path, 'w') as file:
                file.write(new_file_content)
            print(f"Updated <Directory> tag in {idstv_file}")
        except Exception as e:
            print(f"Error writing to file '{idstv_file}': {e}")

# Directory containing the .idstv files
directory_path = "C:\\Users\\SandroP\\OneDrive - Saskarc\\Desktop\\W8787\\W8787-1-L\\"
new_directory_path = "C:\\Users\\SandroP\\OneDrive - Saskarc\\Desktop\\W8787\\W8787-1-L\\"
process_idstv_files(directory_path, new_directory_path)
