import requests

def get_api_key(file_path='api_key.txt'):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# Get the API key from the text file
api_key = get_api_key()

if api_key:
    # Define the endpoint URL
    url = 'https://vast.ai/api/v0/instances?api_key={api_key}'
    headers = {'Accept': 'application/json'}
    params = {
        'user': 'self'  # To get instances belonging to the authenticated user
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        instances = response.json()
        
        # Print information about each instance
        print("Your Instances:")
        for instance in instances:
            print("Instance ID:", instance['id'])
            print("GPU Name:", instance['machine']['gpu_name'])
            print("Dollars Per Hour (DPH):", instance['dph_total'])
            print("SSH Information:")
            print("  Host:", instance['ssh_host'])
            print("  Port:", instance['ssh_port'])
            print("  Username:", instance['ssh_username'])
            print("  Password:", instance['ssh_password'])
            print("-" * 30)
    else:
        print("Failed to retrieve instances. Status code:", response.status_code)
else:
    print("API key could not be retrieved.")

