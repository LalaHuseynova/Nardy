import threading
import webbrowser

from flask import Flask, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

from app import app as human_app
from app_ai import app as ai_app


HOST = "127.0.0.1"
PORT = 5000

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


def open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}/")


def main():
    threading.Timer(1.0, open_browser).start()
    print(f"Nardy launcher is running at http://{HOST}:{PORT}/")
    print("Choose a game mode in the browser. Press Ctrl+C here to stop.")
    run_simple(HOST, PORT, application, use_debugger=True, use_reloader=False)


if __name__ == "__main__":
    main()
