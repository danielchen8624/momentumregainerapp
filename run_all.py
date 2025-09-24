import subprocess

# Start backend
backend = subprocess.Popen(["python", "app/backend/main.py"])

# Start desktop
desktop = subprocess.Popen(["python", "app/desktop/main.py"])

# Wait for both to finish (so the script doesn't exit early)
backend.wait()
desktop.wait()
