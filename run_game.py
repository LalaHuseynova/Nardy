import subprocess
import sys


MODES = {
    "1": ("Human vs Human", "app.py"),
    "2": ("Human vs AI", "app_ai.py"),
}


def choose_mode():
    print("\nNardy game launcher")
    print("===================")
    for key, (label, filename) in MODES.items():
        print(f"{key}. {label} ({filename})")

    while True:
        choice = input("\nChoose mode 1 or 2: ").strip()
        if choice in MODES:
            return MODES[choice]
        print("Invalid choice. Please enter 1 or 2.")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip()
        aliases = {
            "human": "1",
            "hvh": "1",
            "1": "1",
            "ai": "2",
            "human-ai": "2",
            "hva": "2",
            "2": "2",
        }
        mode_key = aliases.get(arg)
        if mode_key is None:
            print("Usage: python run_game.py [1|2|human|ai]")
            return 1
        label, filename = MODES[mode_key]
    else:
        label, filename = choose_mode()

    print(f"\nStarting {label}. Open in your browser.")
    print("Press Ctrl+C here to stop the server.\n")
    try:
        subprocess.run([sys.executable, filename], check=False)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
