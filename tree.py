from RPA.Windows import Windows
import re,os,json,shutil,sys,timeit,time
import psutil
import tracemalloc
import argparse
window = Windows()
#----------------CONFIG--------------------------
PARENT_FOLDER = "application_DOM_data"
APP_DATA_FOLDER = "app_data"
STEPS_FILE = "steps.txt"
# config for print_tree
LOG = False
MAX_DEPTH = 10000
RETURN_STRUCTURE = True # Need this as true for the code to work

#-------------------CODE--------------------------

def get_name(executable):
    windows = window.list_windows()
    for item in windows:
        if item["name"].lower() == executable.lower() or item["path"].lower() == executable.lower():
            return item["title"]

def extract(input_string):
    # Split the input text into lines
    lines = input_string.strip().split("\n")
    # print(lines)
    extracted_data = []
    pattern = r"item=(.*?), locator='(.*?)', name='(.*?)', automation_id='(.*?)', control_type='(.*?)', class_name='(.*?)', left=(\d+), right=(\d+), top=(\d+), bottom=(\d+), width=(\d+), height=(\d+), xcenter=(\d+), ycenter=(\d+)"
    path_re = r"path:(.*)"
    # Loop through each line and extract information
    for line in lines:
        line = line[15:-2]
        match = re.match(pattern, line)
        if match:
            item = match.group(1).strip()
            locator = match.group(2).strip()
            path_match = re.search(path_re,locator)
            if path_match:
                path = path_match.group(1).strip()
            else:
                path = ""
            name = match.group(3).strip()
            automation_id = match.group(4).strip()
            control_type = match.group(5).strip()
            class_name = match.group(6).strip()
            # left = int(match.group(7))
            # right = int(match.group(8))
            # top = int(match.group(9))
            # bottom = int(match.group(10))
            # width = int(match.group(11))
            # height = int(match.group(12))
            # xcenter = int(match.group(13))
            # ycenter = int(match.group(14))
            
            # Create a dictionary for the extracted information
            extracted_info = {
                "item": item,
                "locator": locator,
                "path": path,
                "name": name,
                "automation_id": automation_id,
                "control_type": control_type,
                "class_name": class_name,
                # "left": left,
                # "right": right,
                # "top": top,
                # "bottom": bottom,
                # "width": width,
                # "height": height,
                # "xcenter": xcenter,
                # "ycenter": ycenter,
            }

            # Append the dictionary to the list of extracted data
            extracted_data.append(extracted_info)
        else:
            continue

    # Write the data to the file
    with open(f'{PARENT_FOLDER}\\{APP_DATA_FOLDER}\\tree.txt', 'a', encoding='utf-8') as file:
        for i, data in enumerate(extracted_data):
            file.write(f"Data :\n")
            for key, value in data.items():
                file.write(f"{key}: {value}\n")
            file.write("\n")

def create_tree_json():
    # Initialize a dictionary to store the nested data
    nested_data = {}

    # Open the text file for reading
    with open(f'{PARENT_FOLDER}\\{APP_DATA_FOLDER}\\tree.txt', 'r', encoding='utf-8') as file:
        current_data = {}  # Initialize an empty data dictionary
        current_path = None  # Initialize the current path
        for line in file:
            if line.strip() == "":
                # Empty line indicates the end of a data block, store it by path hierarchy
                if current_path is not None:
                    path_parts = current_path.split('|')
                    parent = nested_data
                    for part in path_parts:
                        if part not in parent:
                            parent[part] = {}
                        parent = parent[part]
                    parent.update(current_data)
                    current_data = {}
                    current_path = None
            else:
                # Parse key and value pairs
                parts = line.strip().split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    current_data[key] = value
                    if key == "path":
                        current_path = value

    # Save the nested data as JSON
    with open(f'{PARENT_FOLDER}\\{APP_DATA_FOLDER}\\tree.json', 'w', encoding='utf-8') as output_file:
        json.dump(nested_data, output_file, indent=4)
            
def launch_window(what_to_run):
    window.windows_run(what_to_run) 
    window.send_keys(keys="{WIN}{UP}")
    name = get_name(what_to_run)
    if name == None:
        print("No program found")
        sys.exit()
    else:
        global APP_DATA_FOLDER
        APP_DATA_FOLDER = f"{name}_version_{time.strftime('%Y%m%d%H%M%S', time.localtime())}"
        time.sleep(10)
        window.control_window(name)

def parse_tree(tree):
    for key in tree.keys():
        for item in tree[key]:
            extract(str(item))
    create_tree_json()

# def explore_tree(tree):
#     for key in tree.keys():
#         for item in tree[key]:
#             if isinstance(item, dict) and "path" in item:
#                 # Extract the path from the current component
#                 path = item["path"]
#                 print(f"Exploring component with path: {path}")
#                 window.print_tree(path=path, max_depth=MAX_DEPTH, log_as_warnings=LOG)
#                 # Recursively explore this component's tree
#                 explore_tree(window.print_tree(
#                     path=path, max_depth=MAX_DEPTH, log_as_warnings=LOG, return_structure=True
#                 ))

def run_additional_steps(filename):
    try:
        with open(filename, 'r') as steps_file:
            for line in steps_file:
                # Remove leading and trailing whitespaces
                step = line.strip()
                if step:
                    print(f"Running step: {step}")
                    exec(step)
    except FileNotFoundError:
        print("Steps file not found.")
        print("Running without additional steps")
    except Exception as e:
        print(f"Error while running steps: {e}")

def get_ram_usage():
    ram = psutil.virtual_memory()
    return f"RAM Usage: {ram}%"

def get_cpu_usage():
    cpu = psutil.cpu_percent(interval=1)
    return f"CPU Usage: {cpu}%"

def main():
    parser = argparse.ArgumentParser(description='Automate Windows application DOM tree extraction')
    parser.add_argument('-i', '--appname', required=True, help='Application name to run')
    parser.add_argument('-o', '--outputpath', required=True, help='Path to write output data')
    args = parser.parse_args()
    global PARENT_FOLDER
    PARENT_FOLDER = args.outputpath
    try:
        if not os.path.exists(PARENT_FOLDER):
            os.mkdir(PARENT_FOLDER)
        what_to_run = args.appname
        launch_window(what_to_run)
        #Get rid of last run data for same application
        # if os.path.exists(f"{PARENT_FOLDER}\\{APP_DATA_FOLDER}"):
        #     shutil.rmtree(f"{PARENT_FOLDER}\\{APP_DATA_FOLDER}")
        # os.mkdir(f"{PARENT_FOLDER}\\{APP_DATA_FOLDER}")
        # if os.path.exists(f"{PARENT_FOLDER}\\{APP_DATA_FOLDER}\\images"):
        #     shutil.rmtree(f"{PARENT_FOLDER}\\{APP_DATA_FOLDER}\\images")
        run_additional_steps(STEPS_FILE)
        os.mkdir(f"{PARENT_FOLDER}\\{APP_DATA_FOLDER}")
        tree = window.print_tree(
            # capture_image_folder=f"{PARENT_FOLDER}\\{APP_DATA_FOLDER}\\images",
            return_structure=RETURN_STRUCTURE,
            max_depth=MAX_DEPTH,
            log_as_warnings=LOG
            )
        parse_tree(tree)
    finally:
        window.close_current_window()
        print(get_cpu_usage())  # Print CPU usage
        
if __name__ == "__main__":
    tracemalloc.start()
    execution_time = timeit.timeit(main, number=1)
    print(f"Execution time: {execution_time} seconds")
    print(f"Memory: {tracemalloc.get_traced_memory()[1]/10**6} MB")
    tracemalloc.stop()
    
    
    
