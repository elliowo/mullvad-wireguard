import json
import random
import urllib.request
import subprocess
import datetime
import os
import sys
 
# Colours
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
NC='\033[0m' # no colour

SERVER_LIST_URL = "https://mullvad.net/media/files/mullvad-wg.sh"
CONFIG_DIR = os.path.expanduser("~/.config/mullvad")
WIREGUARD_DIR = "/etc/wireguard"

def error_log(command: str, error: Exception | None = None):
    error_log_file = os.path.join(CONFIG_DIR, 'error.log')
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Command: {command}"
    if error:
        log_entry += f", Error: {type(error).__name__} - {error}"
    try:
        with open(error_log_file, "a") as log_file:
            log_file.write(log_entry + "\n")
    except IOError as e:
        print(f"Error writing to log file: {e}")

def set_default(server: str):
    default_server_file = os.path.join(CONFIG_DIR, 'default.txt')
    try:
        with open(default_server_file, "w") as default_file:
            default_file.write(server)
    except Exception as e:
        error_log("Error setting default connection", error=e)

def get_default() -> str:
    default_server_file = os.path.join(CONFIG_DIR, 'default.txt')
    try:
        with open(default_server_file, "r") as default_file:
            default_server = default_file.read()
            return default_server
    except Exception as e:
        error_log("Error getting default connection", error=e)
        return "Error getting default connection"

def set_server_list():
    server_list_file = os.path.join(CONFIG_DIR, 'server_list.txt')
    try:
        print(f"Setting server list from " + WIREGUARD_DIR)
        result = subprocess.run(
                ["doas", "ls", WIREGUARD_DIR],
                capture_output=True,
                text=True
            )
        files = result.stdout.split('\n')
        with open(server_list_file, "w") as server_list:
            for file in files:
                if file:
                    if file.endswith('.conf'):
                        cleaned_name = file[:-5]
                        server_list.write(f"{cleaned_name}\n")
    except Exception as e:
        error_log("Error setting server list", error=e)

def get_random(server: str) -> str:
    server_list = get_server_list()
    if not server_list:
        return ""
    line_list = [line for line in server_list.split('\n') if line]
    return random.choice(line_list) if line_list else ""
        
        
def get_server_list() -> str:
    server_list_file = os.path.join(CONFIG_DIR, 'server_list.txt')
    try:
        with open(server_list_file, "r") as server_list:
            return server_list.read()
    except Exception as e:
        error_log("Error getting server list", error=e)
        return "Error getting server list"
    
def help_menu() -> str:
    return(f"""
    
    =========
    HELP MENU
    =========
    
    Available Commands:
    1. {GREEN}connect{NC} <server>         - Connects to the specified server.
    2. {RED}disconnect{NC}               - Disconnects from the active server.
    3. {YELLOW}verify{NC}                   - Verifies your connection.
    
    help              - Brings up this help menu.
    """)

def get_current_connection():
    try:
        result = subprocess.run(
            ["wg", "show", "interfaces"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    
    except Exception as e:
        error_log("Error getting current connection", error=e)
        return None
    
def connect(target_server: str) -> None:
    try:
        current_connection = get_current_connection()
        if current_connection != target_server:
            if current_connection:
                print("Must disconnect before connecting to a new server")
                disconnect()
                
            print(GREEN + "Connecting to " + target_server + NC)
            result = subprocess.run(
                ["doas", "wg-quick", "up", target_server],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"{RED}Error: connecting to server {result.stderr}{NC}")
            verify(get_current_connection())
        else:
            print(RED + "You are already connected to " + target_server + NC)

        return None
    
    except Exception as e:
        error_log("Error connecting to server", error=e)
        return None
            
def disconnect():
    try:
        current_connection = get_current_connection()
        if current_connection:
            print(RED + "Disconnecting VPN " + current_connection + NC)
            result = subprocess.run(
                ["doas", "wg-quick", "down", current_connection],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"{RED}Error: disconnecting from server: {result.stderr}{NC}")
            else:
                print(GREEN + "Successfully disconnected from " + current_connection + NC)
        else:
            print(RED + "You are currently not connected to a server" + NC)

    except Exception as e:
        error_log("Error disconnecting to server", error=e)
        return None

def verify(server):
   try:
       response = urllib.request.urlopen('https://am.i.mullvad.net/json')
       data = json.loads(response.read())
       mullvad_exit_ip = data.get('mullvad_exit_ip', '')

       if mullvad_exit_ip:
           print(GREEN + "Connection verified to " + server + NC)
       else:
           print(RED + "Unable to verify connection to " + server + NC)

       print("VPN Connection Status")
       print("---------------------")
       print(f"IP Address: {data['ip']}")
       print(f"Country: {data['country']}")
       print(f"City: {data['city']}")
       print(f"Longitude: {data['longitude']}")
       print(f"Latitude: {data['latitude']}")
       print(f"VPN Server Type: {data['mullvad_server_type']}")
       print(f"Blacklisted: {data['blacklisted']['blacklisted']}")
       print(f"Exit Status (IP): {data['mullvad_exit_ip']}")
       print(f"Exit Status (Hostname): {data['mullvad_exit_ip_hostname']}")
       
   except Exception as e:
       error_log("Error verifying server", error=e)
       return None
   

def main():
    if len(sys.argv) < 2:
        print(help_menu())
        return
    
    command = sys.argv[1]
    match command:
        case "connect":
            if len(sys.argv) <= 2:
                print("Please specify a server to connect to")
            else:
                target_server = "mullvad-" + sys.argv[2]
                connect(target_server)
            return
        case "help":
            print(help_menu())
            return
        case "default":
            default_server = get_default()

            if default_server:
                print(default_server)
                connect(default_server)
            else:
                if len(sys.argv) <= 2:
                    print("Currently no default server is set")
                    print("Please specify a default server to set")
                else:
                    default_server = "mullvad-" + sys.argv[2]
                    set_default(default_server)
            return
        case "disconnect":
            disconnect()
            return
        case "verify":
            current_connection = get_current_connection()
            verify(current_connection)
            return
        case "random":
            if len(sys.argv) <= 2:
                random_server = get_random()
                if random_server:
                    print("Connecting to "+ YELLOW + random_server + NC)
                    connect(random_server)
                    return
                else:
                    print(f"Unable to get a server. Run {YELLOW}list{NC} to ensure there are servers")
                    return
            else:
                region = sys.argv[2]
                print(f"Finding a server within the region: {YELLOW}{region}{NC}")
                
        case "list":
            server_list = get_server_list()

            if server_list:
                print(server_list)
            else:
                print(f"No server list generated or empty, {YELLOW}attempting generation{NC}")
                set_server_list()
                print("Server list generated, run again to view")
            return

    
if __name__ == "__main__":
    main()
