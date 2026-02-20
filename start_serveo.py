import subprocess
import time
import re
import sys
import os

def start_serveo():
    print("---------------------------------------------------")
    print(" STARTING SERVEO PUBLIC TUNNEL...")
    print("---------------------------------------------------")
    
    # Kill any existing ssh processes to avoid conflicts
    os.system("taskkill /F /IM ssh.exe >nul 2>&1")

    # Use a highly unique subdomain to avoid collisions
    unique_subdomain = "healix-portal-777"
    
    process = subprocess.Popen(
        ["ssh", "-i", "healix_key", "-tt", "-4", "-o", "StrictHostKeyChecking=no", "-R", f"{unique_subdomain}:80:127.0.0.1:5000", "serveo.net"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    url = None
    print(f"Requesting subdomain: {unique_subdomain}.serveo.net")
    print("Waiting for URL...")
    
    # Serveo output usually comes to stdout
    start_time = time.time()
    while time.time() - start_time < 30:
        line = process.stdout.readline()
        if not line:
            break
            
        print(line.strip())
        
        # Regex to find the URL
        # Forwarding HTTP traffic from https://....serveo.net
        match = re.search(r"https://[a-zA-Z0-9-]+\.serveo\.net", line)
        
        if match:
            url = match.group(0)
            # Ensure it's not the generic console URL
            if "console.serveo.net" not in url:
                print(f"\n * SUCCESS! PUBLIC ACCESS URL: {url}\n")
                
                # Save to file
                with open("public_url.txt", "w") as f:
                    f.write(url)
                break
            else:
                url = None # Keep looking
            
    if url:
        print("---------------------------------------------------")
        print(" URL confirmed. Keep this window OPEN.")
        print("---------------------------------------------------")
        # Keep script alive
        while True:
            time.sleep(1)
    else:
        print("Failed to secure unique subdomain. Please check connection or try another name.")
        # Fallback to random subdomain if the specific one fails
        print("Attempting fallback to random subdomain...")
        os.system(f"python start_serveo.py --random") 

if __name__ == "__main__":
    start_serveo()
