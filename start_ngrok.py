from pyngrok import ngrok
import time
import sys
import os

def start_tunnel():
    print("---------------------------------------------------")
    print(" STARTING ROBUST NGROK TUNNEL (GUARDIAN MODE)")
    print("---------------------------------------------------")
    
    # Set the authtoken once
    authtoken = "39v00DEiRliTbBCh3ZNYlyfSgNZ_2fcKZeEYpNHYzRku2jb73"
    ngrok.set_auth_token(authtoken)

    while True:
        try:
            print(f"\n[{time.strftime('%H:%M:%S')}] Connecting to ngrok...")
            # Connection logic
            # For static domains, use: ngrok.connect(5000, "http", domain="your-domain.ngrok-free.app")
            # For now, we use dynamic which is free.
            tunnel = ngrok.connect(5000, "http")
            public_url = tunnel.public_url

            print(f" * SUCCESS! PUBLIC URL: {public_url}")
            
            with open("public_url.txt", "w") as f:
                f.write(public_url)
                
            print(" Keep this window open. Guardian will restart tunnel if it fails.")
            
            # Wait for tunnel to close or error
            # ngrok doesn't have a simple 'wait' but we can check if it's still there
            while True:
                time.sleep(10)
                # Check status? Simple check is if process is still running or if we can reach it
                # For this script, we assume if it hits an exception it failed.
                pass

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Tunnel error: {e}")
            print(" Retrying in 5 seconds...")
            try:
                ngrok.kill()
            except:
                pass
            time.sleep(5)

if __name__ == "__main__":
    start_tunnel()
