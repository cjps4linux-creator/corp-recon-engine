import sys
import threading
import time
import urllib.request
import webview
import uvicorn

# Launch FastAPI backend in a background thread
def start_backend():
    sys.path.insert(0, r'C:\Users\user\corp-recon-engine')
    from launcher import app
    config = uvicorn.Config(app, host='127.0.0.1', port=8765, log_level='warning')
    server = uvicorn.Server(config)
    import asyncio
    asyncio.run(server.serve())

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# Wait for backend to be ready
print("Starting Recon Engine Pro...")
print("Waiting for backend to start...")
for _ in range(120):
    try:
        urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=1)
        print("Backend ready.")
        break
    except Exception:
        time.sleep(1)
else:
    print("Backend did not start in time.")
    sys.exit(1)

# Create desktop window pointing at the web frontend
window = webview.create_window(
    'Recon Engine Pro',
    url='http://127.0.0.1:8765/',
    width=1280,
    height=900,
    resizable=True,
    text_select=True,
)
webview.start()
