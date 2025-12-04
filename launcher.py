#!/usr/bin/env python3
"""
GestureCanvas Desktop App Launcher
===================================
Unified launcher for the PyWebView-based desktop application.
Handles backend startup, port management, and native window creation.
Falls back to browser if PyWebView is unavailable.
"""

import sys
import socket
import threading
import time
import logging
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Launcher")

def find_free_port():
    """Find an available port dynamically"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def start_server(port: int):
    """Start the FastAPI server in a background thread"""
    import uvicorn
    try:
        uvicorn.run(
            "server:app",
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False
        )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

def wait_for_server(port: int, timeout: int = 30) -> bool:
    """Wait for server to be ready with health check"""
    try:
        import requests
    except ImportError:
        logger.warning("requests not installed, skipping health check")
        time.sleep(5)  # Give server time to start
        return True
    
    start_time = time.time()
    url = f"http://127.0.0.1:{port}/health"
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                logger.info("Backend ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    
    return False

def launch_with_pywebview(port: int):
    """Launch using PyWebView native window"""
    try:
        import webview
    except ImportError:
        logger.error("PyWebView not available. Install with: pip install 'pywebview>=4.4.1,<5.0'")
        return False
    
    logger.info("Launching GestureCanvas in native window...")
    try:
        window = webview.create_window(
            title="Gesture Canvas",
            url=f"http://127.0.0.1:{port}",
            width=1280,
            height=800,
            resizable=True,
            frameless=False,
            easy_drag=False,
            min_size=(800, 600),
        )
        webview.start(debug=False)
        return True
    except Exception as e:
        logger.error(f"PyWebView failed: {e}")
        return False

def launch_with_browser(port: int):
    """Fallback: Launch in default browser"""
    url = f"http://127.0.0.1:{port}"
    logger.info(f"Opening GestureCanvas in browser: {url}")
    logger.info("Close the browser tab to exit, or press Ctrl+C here")
    
    try:
        webbrowser.open(url)
        # Keep server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")

def main():
    """Main launcher entry point"""
    # Check if frontend is built
    frontend_dist = Path(__file__).parent / "frontend" / "dist" / "index.html"
    if not frontend_dist.exists():
        logger.error("Frontend not built!")
        logger.error("Please run: cd frontend && npx vite build")
        sys.exit(1)
    
    # Find available port
    port = find_free_port()
    logger.info(f"Starting server on port {port}...")
    
    # Start server in daemon thread
    server_thread = threading.Thread(
        target=start_server,
        args=(port,),
        daemon=True,
        name="FastAPIServer"
    )
    server_thread.start()
    
    # Wait for server to be ready
    if not wait_for_server(port):
        logger.error("Server failed to start within 30 seconds")
        sys.exit(1)
    
    # Try PyWebView first, fallback to browser
    if not launch_with_pywebview(port):
        logger.info("Falling back to browser mode...")
        launch_with_browser(port)

if __name__ == "__main__":
    main()
