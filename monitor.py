import subprocess
import psutil
import os
import winsound
import time

from dotenv import load_dotenv
load_dotenv()

MAX_MEMORY_USAGE_MB = int(os.environ.get("MAX_MEMORY_USAGE_MB"))
MAX_TOTAL_MEMORY_USAGE_PER = int(os.environ.get("MAX_TOTAL_MEMORY_USAGE_PER"))
def beep():
    winsound.Beep(1000, 500)  # Beep at 1000 Hz for 500 milliseconds

def clear_terminal():
    if os.name == 'posix':
        # For Unix/Linux/Mac
        os.system('clear')
    elif os.name == 'nt':
        # For Windows
        os.system('cls')
def conditions(memory_info,cpu_percent,total_used_ram,total_used_cpu,ram_info):
    if memory_info.rss / (1024 * 1024) > MAX_MEMORY_USAGE_MB :
        print("Memory Usage Exceeded")
        return True
    if (ram_info.total - total_used_ram)/ram_info.total > MAX_TOTAL_MEMORY_USAGE_PER:
        print("Total Memory Usage Exceeded")
        return True
    if cpu_percent > 5:
        print("CPU Usage Exceeded")
        return True
        
def launch_script_as_subprocess():
    try:
        print("Enter command to run script (press ENTER to take command from .env):")
        cmd = input()
        if cmd == "":
            cmd = os.environ.get("CMD")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        pid = process.pid
        start_time = time.time()  # Record the start time
        while process.poll() is None:
            try:
                process_obj = psutil.Process(pid)
                cpu_percent = process_obj.cpu_percent()
                memory_info = process_obj.memory_info()
                ram_info = psutil.virtual_memory()
                total_used_ram = ram_info.used // (1024 * 1024)
                total_used_cpu = psutil.cpu_percent()
                print("Script Resource Usage")# Convert to MB
                print(f"\tCPU Percent: {cpu_percent}%")
                print(f"\tMemory Usage: {memory_info.rss / (1024 * 1024):.2f} MB")  # in MB
                print("Total Resource Usage")
                print(f"\tCPU Percent: {total_used_cpu}%")
                print(f"\tMemory Usage: {total_used_ram} MB")
                if conditions(memory_info,cpu_percent,total_used_ram,total_used_cpu,ram_info):
                    process.kill()
                    beep()
                    break
                clear_terminal()
            except psutil.NoSuchProcess:
                break
        end_time = time.time()  # Record the end time
        for line in process.stdout:
            print(line.strip())

        for line in process.stderr:
            print(line.strip())
        
        return_code = process.returncode
        if return_code == 0:
            print("Script executed successfully.")
        else:
            print(f"{return_code}")
            print(f"Script execution failed with return code {return_code}.")
            
        execution_time = end_time - start_time  # Calculate the execution time
        print(f"Memory Usage: {memory_info.rss / (1024 * 1024):.2f} MB")
        print(f"Execution Time: {execution_time} seconds")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    launch_script_as_subprocess()
