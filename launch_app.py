import sys
import threading
import time
import urllib.request

def open_browser():
    time.sleep(2)
    try:
        urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=5)
        import webbrowser
        webbrowser.open('http://127.0.0.1:8765/')
    except Exception:
        pass

def start_backend():
    sys.path.insert(0, r'C:\Users\user\corp-recon-engine')
    from launcher import app
    import uvicorn
    config = uvicorn.Config(app, host='127.0.0.1', port=8765, log_level='warning')
    server = uvicorn.Server(config)
    import asyncio
    asyncio.run(server.serve())

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

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

try:
    import webview
    window = webview.create_window(
        'Recon Engine Pro',
        url='http://127.0.0.1:8765/',
        width=1280,
        height=900,
        resizable=True,
        text_select=True,
    )
    webview.start()
except Exception as e:
    print("PyWebView unavailable, falling back to browser:", e)
    import webbrowser
    webbrowser.open('http://127.0.0.1:8765/')
    input('Press Enter to exit...')
