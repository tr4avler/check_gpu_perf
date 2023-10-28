import requests
import logging
import paramiko
import re

API_KEY_FILE = 'api_key.txt'

# Logging Configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("script_output.log"),
                              logging.StreamHandler()])

# Load API Key
try:
    with open(API_KEY_FILE, 'r') as file:
        api_key = file.read().strip()
except FileNotFoundError:
    logging.error(f"API key file '{API_KEY_FILE}' not found.")
    exit(1)
except Exception as e:
    logging.error(f"Error reading API key: {e}")
    exit(1)

# Define Functions
def test_api_connection():
    """Function to test the API connection."""
    test_url = "https://console.vast.ai/api/v0/"
    try:
        response = requests.get(test_url, headers={"Accept": "application/json"})
        if response.status_code == 200:
            logging.info("Connection with API established and working fine.")
        else:
            logging.error(f"Error connecting to API. Status code: {response.status_code}. Response: {response.text}")
    except Exception as e:
        logging.error(f"Error connecting to API: {e}")

def instance_list():
    """Function to list instances."""
    url = f'https://console.vast.ai/api/v0/instances/?api_key={api_key}'
    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        
        if 'instances' not in response_json:
            logging.error("'instances' key not found in response. Please check the API documentation for the correct structure.")
            return
        instances = response_json['instances']
        
        # Print information about each instance
        logging.info("Your Instances:")
        for instance in instances:
            instance_id = instance.get('id', 'N/A')
            gpu_name = instance.get('gpu_name', 'N/A')
            dph_total = instance.get('dph_total', 'N/A')
            ssh_host = instance.get('ssh_host', 'N/A')
            ssh_port = instance.get('ssh_port', 'N/A')
            username = 'root'
            password = 'your_password'  # Replace with the actual root password
            
            logging.info("Instance ID: %s", instance_id)
            logging.info("GPU Name: %s", gpu_name)
            logging.info("Dollars Per Hour (DPH): %s", dph_total)
            logging.info("SSH Command: ssh -p %s root@%s -L 8080:localhost:8080", ssh_port, ssh_host)
            
            log_info = get_log_info(ssh_host, ssh_port, username, password)
            if log_info:
                logging.info("Log Information:\n%s", log_info)
            else:
                logging.error("Failed to retrieve log information for instance ID: %s", instance_id)
            
            logging.info("-" * 30)
    else:
        logging.error("Failed to retrieve instances. Status code: %s. Response: %s", response.status_code, response.text)

def get_log_info(ssh_host, ssh_port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ssh_host, port=ssh_port, username=username, password=password)
        # Fetch the last line of the log file
        _, stdout, _ = ssh.exec_command("tail -n 1 /root/XENGPUMiner/miner.log")
        last_log_line = stdout.readline().strip()

        # Extract running time and normal blocks
        running_time, normal_blocks = parse_log_line(last_log_line)
        return {
            'running_time': running_time,
            'normal_blocks': normal_blocks
        }
    except Exception as e:
        logging.error("Failed to connect or retrieve log info: %s", e)
        return None
    finally:
        ssh.close()

def parse_log_line(log_line):
    # Regex pattern to extract running time and normal blocks
    pattern = re.compile(r'Mining: \d+ Blocks \[(?P<time>\d{2}:\d{2}:\d{2}), .*normal:(?P<blocks>\d+).*\]')
    match = pattern.search(log_line)
    
    if not match:
        logging.error("Failed to parse log line: %s", log_line)
        return None, None
    
    time_str = match.group('time')
    normal_blocks = int(match.group('blocks'))
    
    # Convert running time to full hours
    time_obj = timedelta(hours=int(time_str.split(':')[0]), 
                         minutes=int(time_str.split(':')[1]), 
                         seconds=int(time_str.split(':')[2]))
    running_time = round(time_obj.total_seconds() / 3600)
    
    return running_time, normal_blocks

# Later in your code, when you call get_log_info, you can access the information like this:
log_info = get_log_info(ssh_host, ssh_port, username, password)
if log_info:
    logging.info("Running Time (hours): %s", log_info['running_time'])
    logging.info("Normal Blocks: %s", log_info['normal_blocks'])
else:
    logging.error("Failed to retrieve log information")

# Test API Connection
test_api_connection()

# List Instances
instance_list()
