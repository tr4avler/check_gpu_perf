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
    """Function to list instances and get SSH information."""
    url = f'https://console.vast.ai/api/v0/instances/?api_key={api_key}'
    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    ssh_info_list = []

    if response.status_code == 200:
        response_json = response.json()

        if 'instances' not in response_json:
            logging.error("'instances' key not found in response. Please check the API documentation for the correct structure.")
            return ssh_info_list
        instances = response_json['instances']

        # Print information about each instance
        logging.info("Your Instances:")
        for instance in instances:
            instance_id = instance.get('id', 'N/A')
            gpu_name = instance.get('gpu_name', 'N/A')
            dph_total = instance.get('dph_total', 'N/A')
            ssh_host = instance.get('ssh_host', 'N/A')
            ssh_port = instance.get('ssh_port', 'N/A')

            logging.info("Instance ID: %s", instance_id)
            logging.info("GPU Name: %s", gpu_name)
            logging.info("Dollars Per Hour (DPH): %s", dph_total)
            logging.info("SSH Command: ssh -p %s root@%s -L 8080:localhost:8080", ssh_port, ssh_host)
            logging.info("-" * 30)

            ssh_info = {
                'instance_id': instance_id,
                'ssh_host': ssh_host,
                'ssh_port': ssh_port
            }
            ssh_info_list.append(ssh_info)

    else:
        logging.error("Failed to retrieve instances. Status code: %s. Response: %s", response.status_code, response.text)

    return ssh_info_list

def get_log_info(ssh_host, ssh_port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ssh_host, port=ssh_port, username=username, password=password)
        _, stdout, _ = ssh.exec_command('tail -n 1 /root/XENGPUMiner/miner.log')
        last_log_line = stdout.read().decode()
        
        # Parsing the log information
        running_time_match = re.search(r'\[(\d+:\d+:\d+),', last_log_line)
        normal_blocks_match = re.search(r'Details=normal:(\d+)', last_log_line)
        
        if running_time_match and normal_blocks_match:
            running_time = running_time_match.group(1)
            normal_blocks = int(normal_blocks_match.group(1))
            
            # Convert running time to hours
            hours, minutes, seconds = map(int, running_time.split(':'))
            total_hours = hours + minutes / 60 + seconds / 3600
            total_hours = round(total_hours)
            
            return {'running_time': total_hours, 'normal_blocks': normal_blocks}
        else:
            logging.error("Failed to parse log information")
            return None
    except Exception as e:
        logging.error("Failed to connect or retrieve log info: %s", e)
        return None
    finally:
        ssh.close()

# Test API Connection
test_api_connection()

# List Instances and Get SSH Information
ssh_info_list = instance_list()
username = "root"
password = "your_password_here"

# Fetch Log Information for Each Instance
for ssh_info in ssh_info_list:
    logging.info("Fetching log info for instance ID: %s", ssh_info['instance_id'])
    log_info = get_log_info(ssh_info['ssh_host'], ssh_info['ssh_port'], username, password)
    if log_info:
        logging.info("Running Time (hours): %s", log_info['running_time'])
        logging.info("Normal Blocks: %s", log_info['normal_blocks'])
    else:
        logging.error("Failed to retrieve log information for instance ID: %s", ssh_info['instance_id'])
