import os
import subprocess
import time
import shutil
import nbformat
import traceback
from dotenv import load_dotenv
from datetime import datetime
from nbconvert.preprocessors import ExecutePreprocessor

# Load environment variables from .env.local
load_dotenv(".env.local")
MACHINE_NUMBER = os.getenv("MACHINE_NUMBER")

# Configuration
REPO_DIR = os.path.dirname(os.path.abspath(__file__))  # Root of the repo
MACHINE_FOLDER = os.path.join(REPO_DIR, f"machine_{MACHINE_NUMBER}")  # Machine-specific folder
RESULTS_DIR = os.path.join(REPO_DIR, "results")  # Where to save processed notebooks
BRANCH = "main"
ROOT_REQUIREMENTS = os.path.join(REPO_DIR, "requirements.txt")  # Global requirements file
LOG_FILE = os.path.join(MACHINE_FOLDER, "log.txt")  # Log file inside machine folder

def write_log(message):
    """Write logs to log.txt inside the machine folder."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{timestamp} - {message}\n")

def log_exception(e):
    """Log detailed error traceback and move the notebook to results."""
    error_message = f"Exception occurred:\n{traceback.format_exc()}"
    print(error_message)
    write_log(error_message)
    move_notebook(error_occurred=True)  # Move the notebook even if execution failed
    push_log()

def pull_repo():
    """Pull the latest changes from GitHub and install root dependencies"""
    try:
        print("Pulling latest changes from GitHub...")
        subprocess.run(["git", "pull", "origin", BRANCH], cwd=REPO_DIR, check=True)
        
        if os.path.exists(ROOT_REQUIREMENTS):
            print("Installing/updating global requirements from root requirements.txt...")
            subprocess.run(["pip", "install", "-r", ROOT_REQUIREMENTS], check=True)
    
    except subprocess.CalledProcessError as e:
        log_exception(e)

def run_notebook():
    """Executes the run.ipynb Jupyter Notebook and saves outputs"""
    notebook_path = os.path.join(MACHINE_FOLDER, "run.ipynb")

    if not os.path.exists(notebook_path):
        message = f"No run.ipynb found in {MACHINE_FOLDER}. Going back to listening..."
        print(message)
        write_log(message)
        return False

    print(f"Running notebook: {notebook_path}")

    try:
        # Load the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")

        # Execute the notebook and store outputs
        ep.preprocess(nb, {"metadata": {"path": MACHINE_FOLDER}})

        # Save the executed notebook (WITH OUTPUTS)
        with open(notebook_path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        print("Notebook execution completed successfully.")
        write_log("Notebook execution completed successfully.")
        move_notebook(error_occurred=False)  # Move successfully executed notebook
        return True

    except Exception as e:
        log_exception(e)
        return False

def move_notebook(error_occurred=False):
    """Moves run.ipynb to results/ and renames it, ensuring outputs are saved."""
    notebook_path = os.path.join(MACHINE_FOLDER, "run.ipynb")

    if os.path.exists(notebook_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
        status = "error" if error_occurred else "success"
        new_name = f"run_{MACHINE_NUMBER}_{status}_{timestamp}.ipynb"
        new_path = os.path.join(RESULTS_DIR, new_name)
        
        shutil.move(notebook_path, new_path)
        print(f"Moved run.ipynb to {new_path} (Includes Outputs)")
        write_log(f"Moved notebook to {new_path} (status: {status}, includes outputs)")
        return new_path
    return None

def push_log():
    """Pushes the log file to GitHub so errors can be tracked remotely"""
    try:
        print("Pushing log file to GitHub...")
        subprocess.run(["git", "add", LOG_FILE], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"Machine {MACHINE_NUMBER}: Updated log.txt"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push", "origin", BRANCH], cwd=REPO_DIR, check=True)
        print("Log file pushed successfully.")
        write_log("Log file pushed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error pushing log file: {e}")

def push_results():
    """Commits and pushes changes to GitHub"""
    try:
        print("Pushing changes to GitHub...")
        subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"Machine {MACHINE_NUMBER}: Processed and updated run.ipynb"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push", "origin", BRANCH], cwd=REPO_DIR, check=True)
        print("Changes pushed successfully.")
        write_log("Changes pushed successfully.")
    except subprocess.CalledProcessError as e:
        log_exception(e)

def check_for_changes():
    """Checks if there are any new changes in the repository"""
    last_commit = None
    while True:
        try:
            subprocess.run(["git", "fetch"], cwd=REPO_DIR, check=True)
            new_commit = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, cwd=REPO_DIR, check=True).stdout.strip()

            if new_commit != last_commit:
                print("New changes detected! Processing...")
                write_log("New changes detected, processing...")
                last_commit = new_commit
                pull_repo()

                if run_notebook():
                    push_results()  # Push changes only if a notebook was processed
            
        except subprocess.CalledProcessError as e:
            log_exception(e)
        
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    check_for_changes()
