import uvicorn
import subprocess
import os

if __name__ == "__main__":
    # 1. Start the Frontend in the background
    # Adjust "npm start" and "cwd" to match your frontend setup
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"], 
        cwd="./Frontend",  # Path to your frontend folder
        shell=True         # Required on Windows for npm commands
    )

    try:
        # 2. Start the Backend (Blocking call)
        uvicorn.run("Backend.app:app", host="0.0.0.0", port=8000, reload=True)
    finally:
        # 3. Cleanup: Kill frontend when backend stops
        frontend_process.terminate()
