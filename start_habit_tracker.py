import os
import sys
import subprocess

def ensure_virtualenv():
    # Define the virtual environment path
    venv_path = os.path.join(os.getcwd(), 'venv')  # Assuming the virtual environment is named 'venv'

    # Check if the virtual environment exists
    if not os.path.exists(venv_path):
        print("Virtual environment not found. Creating one...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("Virtual environment created.")

    # Modify the system path to use the virtual environment
    activate_venv(venv_path)

def activate_venv(venv_path):
    # Path to the virtual environment's executable
    if os.name == 'nt':
        python_executable = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:
        python_executable = os.path.join(venv_path, 'bin', 'python')

    # Set the virtual environment's Python executable as the default
    sys.executable = python_executable
    print(f"Virtual environment activated using {venv_path}")

def install_requirements():
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        print(f"Installing packages from {requirements_file}...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], check=True)
        print("All requirements installed.")
    else:
        print(f"No {requirements_file} found. Skipping dependency installation.")

def run_streamlit_app():
    # Get the absolute path to app.py
    app_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    if not os.path.exists(app_file):
        print(f"Error: {app_file} does not exist.")
        sys.exit(1)

    # Run the streamlit app
    streamlit_command = [sys.executable, "-m", "streamlit", "run", app_file]
    subprocess.run(streamlit_command)

if __name__ == "__main__":
    ensure_virtualenv()
    install_requirements()
    run_streamlit_app()
