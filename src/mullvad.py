import json
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
ERROR_LOG_FILE = os.path.join(CONFIG_DIR, 'error.log')
WIREGUARD_DIR = "/etc/wireguard"

def error_log(command: str, error: Exception | None = None):
    """
    Log commands and errors to a file.

    Args:
        command: The command that was executed.
        error: The exception object if an error occurred, otherwise None.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Command: {command}"
    if error:
        log_entry += f", Error: {type(error).__name__} - {error}"
    try:
        with open(ERROR_LOG_FILE, "a") as log_file:
            log_file.write(log_entry + "\n")
    except IOError as e:
        print(f"Error writing to log file: {e}")

def help_menu():
    print(f"""
    
    =========
    HELP MENU
    =========
    
    Available Commands:
    1. {GREEN}connect{NC} <server>         - Connects to the specified server.
    2. {RED}disconnect{NC}               - Disconnects from the active server.
    3. {YELLOW}status{NC}                   - Shows current connection status.
    4. {GREEN}verify{NC}                   - Verifies your connection.
    
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
        error_log(f"Error getting current connection: {e}", error=e)
        return None
    
def connect(target_server: str) -> None:
    try:
        current_connection = get_current_connection()
        if current_connection != target_server:
            if current_connection:
                print("Must disconnect before connecting to a new server")
                disconnect()
                
            print(GREEN + "Connecting to " + target_server + NC)
            subprocess.run(
                ["doas", "wg-quick", "up", target_server],
                capture_output=True,
                text=True
            )
            verify(get_current_connection())
        else:
            print(RED + "You are already connected to " + target_server + NC)

        return None
    
    except Exception as e:
        error_log(f"Error connecting to server: {e}", error=e)
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
                print("\033[91mError: wg-quick down command failed: " + result.stderr + "\033[0m")
            else:
                print(GREEN + "Successfully disconnected from " + current_connection + NC)
        else:
            print(RED + "You are currently not connected to a server" + NC)

    except Exception as e:
        error_log(f"Error disconnecting to server: {e}", error=e)
        return None

def status():
    try:
        current_connection = get_current_connection()
        if current_connection:
            print(GREEN + "Wireguard currently connected to: " + current_connection + NC)
        else:
            print(RED + "VPN Status: Not connected." + NC)

    except:
        error_log(f"Error getting status: {e}", error=e)
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
       error_log(f"Error verifying server: {e}", error=e)
       return None
   

def main():
    if len(sys.argv) < 2:
        help_menu()
        return
    
    command = sys.argv[1]
    match command:
        case "help":
            help_menu()
        case "connect":
            if len(sys.argv) <= 2:
                print("Please specify a server to connect to")
            else:
                target_server = "mullvad-" + sys.argv[2]
                connect(target_server)
            return

        case "status":
            status()
            return

        case "disconnect":
            disconnect()
            return
        
        case "verify":
            current_connection = get_current_connection()
            verify(current_connection)
            return

        case "random":
            pass
  
if __name__ == "__main__":
    main()
