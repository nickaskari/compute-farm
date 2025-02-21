import os
import subprocess
import time
import shutil
import nbformat
from datetime import datetime
from nbconvert.preprocessors import ExecutePreprocessor

# Configuration
REPO_DIR = os.path.dirname(os.path.abspath(__file__))  # Root of the repo
PLAYGROUND_DIR = os.path.join(REPO_DIR, "playground")  # Where the notebook is
RESULTS_DIR = os.path.join(REPO_DIR, "results")  # Where to save processed notebooks
BRANCH = "main"

def pull_repo():
    """Pull the latest changes from GitHub"""
    print("Pulling latest changes from GitHub...")
    subprocess.run(["git", "pull", "origin", BRANCH], cwd=REPO_DIR)

def install_requirements():
    """Installs the packages from the playground/requirements.txt"""
    req_file = os.path.join(PLAYGROUND_DIR, "requirements.txt")
    if os.path.exists(req_file):
        print("Installing dependencies...")
        subprocess.run(["pip", "install", "-r", req_file])

def uninstall_requirements():
    """Uninstalls the packages listed in playground/requirements.txt"""
    req_file = os.path.join(PLAYGROUND_DIR, "requirements.txt")
    if os.path.exists(req_file):
        print("Uninstalling dependencies...")
        with open(req_file, "r") as f:
            packages = f.read().splitlines()
        subprocess.run(["pip", "uninstall", "-y"] + packages)

def run_notebook():
    """Executes the run.ipynb Jupyter Notebook safely"""
    notebook_path = os.path.join(PLAYGROUND_DIR, "run.ipynb")

    if not os.path.exists(notebook_path):
        print("No run.ipynb found. Skipping execution.")
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
        ep.preprocess(nb, {"metadata": {"path": PLAYGROUND_DIR}})

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

def clean_up():
    """Deletes all files in playground/ except run.ipynb"""
    print("Cleaning up playground folder...")
    for file in os.listdir(PLAYGROUND_DIR):
        file_path = os.path.join(PLAYGROUND_DIR, file)
        if file != "run.ipynb":  # Keep only run.ipynb
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

def move_notebook():
    """Moves run.ipynb to results/ and renames it with timestamp"""
    notebook_path = os.path.join(PLAYGROUND_DIR, "run.ipynb")

    if os.path.exists(notebook_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
        new_name = f"run_{timestamp}.ipynb"
        new_path = os.path.join(RESULTS_DIR, new_name)
        
        shutil.move(notebook_path, new_path)
        print(f"Moved run.ipynb to {new_path}")
        return new_path
    return None

def push_results():
    """Commits and pushes changes to GitHub"""
    print("Pushing changes to GitHub...")
    subprocess.run(["git", "add", "."], cwd=REPO_DIR)
    subprocess.run(["git", "commit", "-m", "Processed and updated run.ipynb"], cwd=REPO_DIR)
    subprocess.run(["git", "push", "origin", BRANCH], cwd=REPO_DIR)
    print("Changes pushed successfully.")

def check_for_changes():
    """Checks if there are any new changes in the playground folder"""
    last_commit = None
    while True:
        subprocess.run(["git", "fetch"], cwd=REPO_DIR)
        new_commit = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, cwd=REPO_DIR).stdout.strip()

        if new_commit != last_commit:
            print("New changes detected! Processing...")
            last_commit = new_commit
            pull_repo()
            install_requirements()
            
            if run_notebook():
                uninstall_requirements()
                clean_up()
                renamed_file = move_notebook()
                if renamed_file:
                    push_results()  # Push changes only if something was processed
            
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    check_for_changes()

