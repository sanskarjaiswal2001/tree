import subprocess
import psutil
import os

def clear_terminal():
    if os.name == 'posix':
        # For Unix/Linux/Mac
        os.system('clear')
    elif os.name == 'nt':
        # For Windows
        os.system('cls')
        
def launch_script_as_subprocess():
    try:
        cmd = ["python", "tree.py", "-i", "chrome.exe", "-o", "chrome"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        pid = process.pid
        
        while process.poll() is None:
            try:
                process_obj = psutil.Process(pid)
                cpu_percent = process_obj.cpu_percent()
                memory_info = process_obj.memory_info()
                print(f"CPU Percent: {cpu_percent}%")
                print(f"Memory Usage: {memory_info.rss / (1024 * 1024):.2f} MB")  # in MB
                clear_terminal()
            except psutil.NoSuchProcess:
                break
            
        for line in process.stdout:
            print(line.strip())

        for line in process.stderr:
            print(line.strip())
        
        return_code = process.returncode
        if return_code == 0:
            print("Script executed successfully.")
        else:
            print(f"Script execution failed with return code {return_code}.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    launch_script_as_subprocess()
