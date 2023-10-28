import requests
import logging

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
            logging.info("Instance ID: %s", instance.get('id', 'N/A'))
            logging.info("GPU Name: %s", instance.get('gpu_name', 'N/A')) 
            logging.info("Dollars Per Hour (DPH): %s", instance.get('dph_total', 'N/A'))
            logging.info("SSH Information:")
            logging.info("  SSH: %s", instance.get('ssh_host', 'N/A'))
            logging.info("  Port: %s", instance.get('ssh_port', 'N/A'))
            logging.info("-" * 30)
    else:
        logging.error("Failed to retrieve instances. Status code: %s. Response: %s", response.status_code, response.text)



# Test API Connection
test_api_connection()

# List Instances
instance_list()
