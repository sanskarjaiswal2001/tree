from RPA.Windows import Windows
import re,os,json,sys,timeit,time,platform
import psutil
from dotenv import load_dotenv
import logging
import tracemalloc
import argparse
from uiautomation import *
window = Windows()
load_dotenv()
#----------------Minimum Requirements------------
CPU_CORES = int(os.environ.get("CPU_CORES"))
RAM = int(os.environ.get("RAM"))


#----------------CONFIG--------------------------
logging.basicConfig(filename='automation.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
SCRIPT_NAME = os.environ.get("SCRIPT_NAME")
MAX_CPU_USAGE = int(os.environ.get("MAX_CPU_USAGE")) #%
PARENT_FOLDER = os.environ.get("PARENT_FOLDER")
APP_DATA_FOLDER = os.environ.get("APP_DATA_FOLDER")
STEPS_FILE = os.environ.get("STEPS_FILE")
SLEEP_TIME = int(os.environ.get("SLEEP_TIME"))
GET_SCREENSHOT = bool(int(os.environ.get("GET_SCREENSHOT")))
# config for print_tree rpaframework in-built function
LOG = bool(int(os.environ.get("LOG")))
MAX_DEPTH = int(os.environ.get("MAX_DEPTH"))

# NOTE : Need this as true for the code to generate tree.json and tree.txt
RETURN_STRUCTURE =  bool(int(os.environ.get("RETURN_STRUCTURE")))

#-------------------CODE--------------------------

def get_name(executable):
    windows = window.list_windows()
    for item in windows:
        if item["name"].lower() == executable.lower() or item["path"].lower() == executable.lower():
            logging.info(f"Window found for {executable}")
            return item["title"]
    logging.error(f"Window not found for {executable}")

def extract(input_string):
    # Split the input text into lines
    lines = input_string.strip().split("\n")
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
    logging.info(f"Extracted data from {PARENT_FOLDER}\\{APP_DATA_FOLDER}\\tree.txt")
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
    logging.info(f"Created {PARENT_FOLDER}\\{APP_DATA_FOLDER}\\tree.json")
def launch_window(what_to_run):
    window.windows_search(what_to_run) 
    name = get_name(what_to_run)
    if name == None:
        print("No program found")
        sys.exit()
    else:
        global APP_DATA_FOLDER
        APP_DATA_FOLDER = f"{name}_version_{time.strftime('%Y%m%d%H%M%S', time.localtime())}"
        time.sleep(SLEEP_TIME)
        window.control_window(name)
        logging.info(f"Launched {name}")

def parse_tree(tree):
    for key in tree.keys():
        for item in tree[key]:
            extract(str(item))
    create_tree_json()
    logging.info(f"parsed tree succesfully")

def run_additional_steps(filename):
    try:
        with open(filename, 'r') as steps_file:
            i = 0
            image_location = "images"
            os.mkdir(image_location)
            for line in steps_file:
                # Remove leading and trailing whitespaces
                step = line.strip()
                if step:
                    print(f"Running step: {step}")
                    exec(step)
                    if GET_SCREENSHOT:
                        i+=1
                        image_name = f"{step}.png"
                        window.screenshot(locator=None,filename=f'{image_location}\\{image_name}')
    except FileNotFoundError:
        print("Steps file not found.")
        print("Running without additional steps")
        logging.error(f"Steps file not found.")
    except Exception as e:
        print(f"Error while running steps: {e}")
        logging.error(f"Error while running steps: {e}")

def get_ram_usage():
    ram = psutil.virtual_memory()
    return f"RAM Usage: {ram}%"

def get_cpu_usage():
    cpu = psutil.cpu_percent(interval=1)
    return f"CPU Usage: {cpu}%"

def check_minimum_requirements():
    total_cores = psutil.cpu_count()
    print(f"Total Cores: {total_cores}")
    ram_info = psutil.virtual_memory()
    total_ram = ram_info.total // 10**6
    print(f"Total RAM: {total_ram} MB") 
    if total_cores >= CPU_CORES and total_ram >= RAM:
        logging.info(f"Minimum requirements met. Continuing with execution.")
        return True
    else:
        logging.error(f"Minimum requirements not met. Please check the requirements and try again.")
        return False
    
def get_system_info(output_file_path,when_was_this_logged):
    try:
        # Get system information
        heading = f"============================{when_was_this_logged}========================================"
        total_cores = f"Total Cores :{psutil.cpu_count()}\n"
        physical_cores = f"Physical Cores :{psutil.cpu_count(logical=False)}\n"
        cpu_frequency = f"CPU Frequency :{psutil.cpu_freq()}\n"
        disk_usage = f"Disk Usage:\n{psutil.disk_usage('/')}\n"
        network_info = f"Network Info:\n{psutil.net_if_stats()}\n"

        # Combine all the information
        system_info = (
            heading +
            total_cores +
            physical_cores +
            cpu_frequency +
            disk_usage
        )
        # Save the information to a text file
        with open(output_file_path, 'a') as file:
            file.write(system_info)

        print(f"System information saved to {output_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main_logic():
    parser = argparse.ArgumentParser(description='Automate Windows application DOM tree extraction')
    parser.add_argument('-i', '--appname', required=True, help='Application name or complete path to exe to run')
    parser.add_argument('-o', '--outputpath', required=True, help='Path to write output data to')
    args = parser.parse_args()
    global PARENT_FOLDER
    PARENT_FOLDER = args.outputpath
    try:
        if not os.path.exists(PARENT_FOLDER):
            os.mkdir(PARENT_FOLDER)
        what_to_run = args.appname
        launch_window(what_to_run)
        run_additional_steps(STEPS_FILE)
        if RETURN_STRUCTURE:
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

if __name__ == "__main__":
    if check_minimum_requirements():
        tracemalloc.start()
        execution_time = timeit.timeit(main_logic, number=1)
        print(f"Execution time: {execution_time} seconds")
        print(f"Memory: {tracemalloc.get_traced_memory()[1]/10**6} MB")
        tracemalloc.stop()
    else:
        print(f"Minimum requirements not met. Please check the requirements and try again.")
    
    
    
