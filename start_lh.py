import subprocess
import time
import re
import sys
import os

def start_localhost_run():
    print("---------------------------------------------------")
    print(" STARTING LOCALHOST.RUN TUNNEL...")
    print("---------------------------------------------------")
    
    # Kill any existing ssh processes to avoid conflicts
    os.system("taskkill /F /IM ssh.exe >nul 2>&1")

    process = subprocess.Popen(
        ["ssh", "-4", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:5000", "nokey@localhost.run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    url = None
    print("Waiting for URL...")
    
    start_time = time.time()
    
    while True:
        # Check for timeout
        if time.time() - start_time > 30:
            print("Timeout waiting for URL.")
            break

        line = process.stdout.readline()
        if not line:
            # Try stderr if stdout empty?
            line = process.stderr.readline()
            if not line:
                if process.poll() is not None:
                    break
                time.sleep(0.1)
                continue
            
        print(line.strip())
        
        # Regex for localhost.run
        # usually: "Content accessible at https://xyz.localhost.run" or similar
        # or just the text
        if "localhost.run" in line and "https://" in line:
            match = re.search(r"https://[a-zA-Z0-9-]+\.localhost\.run", line)
            if match:
                url = match.group(0)
                print(f"\n * PUBLIC ACCESS URL: {url}\n")
                
                with open("public_url.txt", "w") as f:
                    f.write(url)
                break
            
    if url:
        print("---------------------------------------------------")
        print(" URL saved. Keep this window OPEN.")
        print("---------------------------------------------------")
        while True:
            time.sleep(1)
    else:
        print("Failed to get URL.")
        print("STDERR:", process.stderr.read())

if __name__ == "__main__":
    start_localhost_run()
