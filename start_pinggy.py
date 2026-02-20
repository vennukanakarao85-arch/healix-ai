import subprocess
import time
import re
import sys

def get_url():
    print("Launching Pinggy tunnel...")
    process = subprocess.Popen(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-p", "443", "-R0:localhost:5000", "a.pinggy.io"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    start_time = time.time()
    url = None
    
    try:
        while time.time() - start_time < 30:
            # Read line by line from stdout
            line = process.stdout.readline()
            if not line:
                break
                
            print(f"OUTPUT: {line.strip()}")
            
            # Look for URL pattern
            match = re.search(r"https://[a-zA-Z0-9-]+\.a\.pinggy\.io", line)
            if match:
                url = match.group(0)
                print(f"FOUND URL: {url}")
                with open("public_url.txt", "w") as f:
                    f.write(url)
                return url
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Don't kill it immediately if found, keep it running?
        # But for this script purpose, we just want the URL.
        # Actually, if we kill it, the tunnel closes.
        # We need to keep it running.
        pass

    if url:
        print("Tunnel established. Keeping script alive.")
        while True:
            time.sleep(1)
    else:
        print("Failed to find URL.")
        process.kill()

if __name__ == "__main__":
    get_url()
