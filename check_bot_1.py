import re

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
        
        # Clean ANSI codes from the log line
        last_line = clean_ansi_codes(last_line)
        
        # Parse the last line to get the required information
        pattern = re.compile(r'Mining:.*\[(\d+):(\d+):(\d+),.*(?:Details=normal:(\d+)|Details=xuni:(\d+)).*\]')
        match = pattern.search(last_line)
        if match:
            # Extracting the running time and normal blocks
            hours, minutes, seconds, normal_blocks, xuni_blocks = match.groups()
            blocks = int(normal_blocks) if normal_blocks is not None else int(xuni_blocks) if xuni_blocks is not None else None
            
            if blocks is not None:
                return int(hours), int(minutes), int(seconds), blocks
            else:
                logging.error("Failed to extract block information")
                return None, None, None, None
        else:
            logging.error("Failed to parse the log line")
            return None, None, None, None
        
    except Exception as e:
        logging.error("Failed to connect or retrieve log info: %s", e)
        return None, None, None, None
    
    finally:
        ssh.close()
