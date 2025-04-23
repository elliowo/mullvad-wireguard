import json
import glob
import urllib.request
import subprocess
import os
import sys
 
# Colours
RED='\033[91m'
GREEN='\033[92m'
NC='\033[0m'

SERVER_LIST_URL =  "https://mullvad.net/media/files/mullvad-wg.sh"
WIREGUARD_DIR = "/etc/wireguard"

def get_current_connection():
    try:
        result = subprocess.run(
            ["wg", "show", "interfaces"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return None
    
def connect(target_server):
    try:
        current_connection = get_current_connection()
        if current_connection != target_server:
            print(GREEN + "Connecting to " + target_server + NC)
            subprocess.run(
                ["doas", "wg-quick", "up", target_server],
                capture_output=True,
                text=True
            )
            verify(get_current_connection())
        else:
            print(RED + "You are already connected to " + target_server + NC)
            
    except:
        print("exception")

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

    except:
        pass

def status():
    try:
        current_connection = get_current_connection()
        if current_connection:
            print(GREEN + "Wireguard currently connected to: " + current_connection + NC)
        else:
            print(RED + "VPN Status: Not connected." + NC)

    except:
        print("exception")

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
       
   except:
       pass
   

def main():
    if len(sys.argv) < 1:
        print("Usage: python script.py command [args...]")
        return

    command = sys.argv[1]
    match command:
        case "connect":
            target_server = "mullvad-" + sys.argv[2]
            connect(target_server)
            return
        case "status":
            status()
        case "disconnect":
            disconnect()
        case "verify":
            current_connection = get_current_connection()
            verify(current_connection)
        case "random":
            pass

  
if __name__ == "__main__":
    main()
