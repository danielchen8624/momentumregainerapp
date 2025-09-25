# run_all.py
import subprocess, sys, time, socket

def wait_for_port(host, port, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False

backend = subprocess.Popen(
    ["python", "-m", "uvicorn", "app.backend.main:app", "--host", "127.0.0.1", "--port", "4545", "--reload"]
)
if not wait_for_port("127.0.0.1", 4545, timeout=20):
    print("Backend failed to start on 127.0.0.1:4545")
    backend.terminate()
    sys.exit(1)

desktop = subprocess.Popen([sys.executable, "app/desktop/main.py"])
backend.wait(); desktop.wait()
