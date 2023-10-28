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

def clean_ansi_codes(input_string):
    ansi_escape = re.compile(r'(?:\x1b\[|\x1b\])[^0-9a-zA-Z]*[0-9a-zA-Z]', re.IGNORECASE)
    return text

def get_log_info(ssh_host, ssh_port, username):
    private_key_path = "/home/admin/.ssh/id_ed25519"
    
    # Create an SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Load the private key
        key = paramiko.Ed25519Key(filename=private_key_path)
        
        # Connect to the server
        ssh.connect(ssh_host, port=ssh_port, username=username, pkey=key)
        
        # Execute the command to get the log information
        _, stdout, _ = ssh.exec_command('tail -n 1 /root/XENGPUMiner/miner.log')
        last_line = stdout.read().decode().strip()
        logging.info("Raw log line: %s", last_line)
        last_line = clean_ansi_codes(last_line)
        
        # Extract running time and normal blocks using regex
        running_time_match = re.search(r'\[(\d+):(\d+):(\d+)', last_line)
        normal_blocks_match = re.search(r'Details=normal:(\d+)', last_line)
        
        if running_time_match and normal_blocks_match:
            hours, minutes, seconds = map(int, running_time_match.groups())
            total_hours = hours + minutes / 60 + seconds / 3600
            total_hours = round(total_hours, 2)  # Keep two decimal places
            normal_blocks = normal_blocks_match.group(1)
            return total_hours, normal_blocks
        else:
            logging.error("Failed to parse log line. Log line: %s", last_line)
            return None, None
        
    except Exception as e:
        logging.error("Failed to connect or retrieve log info: %s", e)
        return None, None
    
    finally:
        ssh.close()

# Test API Connection
test_api_connection()

# List Instances and Get SSH Information
ssh_info_list = instance_list()
username = "root"
password = ""

# Fetch Log Information for Each Instance
for ssh_info in ssh_info_list:
    instance_id = ssh_info['instance_id']
    ssh_host = ssh_info['ssh_host']
    ssh_port = ssh_info['ssh_port']

    logging.info("Fetching log info for instance ID: %s", instance_id)
    total_hours, normal_blocks = get_log_info(ssh_host, ssh_port, username)
    
    if total_hours is not None and normal_blocks is not None:
        logging.info("Running Time (hours): %s", total_hours)
        logging.info("Normal Blocks: %s", normal_blocks)
    else:
        logging.error("Failed to retrieve log information for instance ID: %s", instance_id)
