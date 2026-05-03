import threading
import webbrowser
import socket

from flask import Flask, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

from app import app as human_app
from app_ai import app as ai_app


HOST = "127.0.0.1"
DEFAULT_PORT = 5050

launcher = Flask(__name__)


@launcher.route("/")
def mode_select():
    return render_template("mode_select.html")


application = DispatcherMiddleware(
    launcher,
    {
        "/human": human_app,
        "/ai": ai_app,
    },
)


def find_free_port(start_port=DEFAULT_PORT):
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((HOST, port)) != 0:
                return port
    raise RuntimeError("No free port found for the Nardy launcher.")


def open_browser(port):
    webbrowser.open(f"http://{HOST}:{port}/")


def main():
    port = find_free_port()
    threading.Timer(1.0, open_browser, args=(port,)).start()
    print(f"Nardy launcher is running at http://{HOST}:{port}/")
    print("Choose a game mode in the browser. Press Ctrl+C here to stop.")
    run_simple(HOST, port, application, use_debugger=True, use_reloader=False)


if __name__ == "__main__":
    main()
