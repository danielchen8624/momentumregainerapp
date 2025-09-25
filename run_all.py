# run_all.py
import subprocess, sys, time, socket, os, signal

def wait_for_port(host: str, port: int, timeout: int = 20) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False

def main():
    py = sys.executable  # ensures we use the current venv
    backend_cmd = [
        py, "-m", "uvicorn", "app.backend.main:app",
        "--host", "127.0.0.1", "--port", "4545", "--reload"
    ]

    # Start backend first
    backend = subprocess.Popen(backend_cmd)

    try:
        if not wait_for_port("127.0.0.1", 4545, timeout=25):
            print("Backend failed to start on 127.0.0.1:4545")
            backend.terminate()
            backend.wait(timeout=5)
            sys.exit(1)

        # Start desktop after backend is ready
        desktop = subprocess.Popen([py, "app/desktop/main.py"])

        # Wait for either to exit; then bring down the other
        while True:
            b_ret = backend.poll()
            d_ret = desktop.poll()
            if b_ret is not None or d_ret is not None:
                break
            time.sleep(0.2)

    except KeyboardInterrupt:
        pass
    finally:
        # Graceful shutdown
        for proc in [desktop if 'desktop' in locals() else None, backend]:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()

if __name__ == "__main__":
    main()
