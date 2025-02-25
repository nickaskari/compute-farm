import os
import subprocess
import time
import shutil
import nbformat
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

def pull_repo():
    """Pull the latest changes from GitHub and install root dependencies"""
    print("Pulling latest changes from GitHub...")
    subprocess.run(["git", "pull", "origin", BRANCH], cwd=REPO_DIR)

    if os.path.exists(ROOT_REQUIREMENTS):
        print("Installing/updating global requirements from root requirements.txt...")
        subprocess.run(["pip", "install", "-r", ROOT_REQUIREMENTS])

def run_notebook():
    """Executes the run.ipynb Jupyter Notebook if it exists"""
    notebook_path = os.path.join(MACHINE_FOLDER, "run.ipynb")

    if not os.path.exists(notebook_path):
        print(f"No run.ipynb found in {MACHINE_FOLDER}. Going back to listening...")
        return False

    print(f"Running notebook: {notebook_path}")

    try:
        # Ensure the file is a valid Jupyter Notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if not first_line.startswith("{") and not first_line.startswith("["):
                raise ValueError("The file is not a valid Jupyter Notebook (not JSON format).")

        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        ep.preprocess(nb, {"metadata": {"path": MACHINE_FOLDER}})

        with open(notebook_path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        print("Notebook execution completed successfully.")
        return True

    except ValueError as ve:
        print(f"Error: {ve}")
        return False
    except Exception as e:
        print(f"Notebook execution failed: {e}")
        return False

def move_notebook():
    """Moves run.ipynb to results/ and renames it with timestamp"""
    notebook_path = os.path.join(MACHINE_FOLDER, "run.ipynb")

    if os.path.exists(notebook_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
        new_name = f"run_{MACHINE_NUMBER}_{timestamp}.ipynb"
        new_path = os.path.join(RESULTS_DIR, new_name)
        
        shutil.move(notebook_path, new_path)
        print(f"Moved run.ipynb to {new_path}")
        return new_path
    return None

def push_results():
    """Commits and pushes changes to GitHub"""
    print("Pushing changes to GitHub...")
    subprocess.run(["git", "add", "."], cwd=REPO_DIR)
    subprocess.run(["git", "commit", "-m", f"Machine {MACHINE_NUMBER}: Processed and updated run.ipynb"], cwd=REPO_DIR)
    subprocess.run(["git", "push", "origin", BRANCH], cwd=REPO_DIR)
    print("Changes pushed successfully.")

def check_for_changes():
    """Checks if there are any new changes in the repository"""
    last_commit = None
    while True:
        subprocess.run(["git", "fetch"], cwd=REPO_DIR)
        new_commit = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, cwd=REPO_DIR).stdout.strip()

        if new_commit != last_commit:
            print("New changes detected! Processing...")
            last_commit = new_commit
            pull_repo()

            if run_notebook():
                renamed_file = move_notebook()
                if renamed_file:
                    push_results()  # Push changes only if a notebook was processed
            
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    check_for_changes()
