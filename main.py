import os
import subprocess
import time
import shutil
import nbformat
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
    """Runs the run.py script as a Jupyter Notebook"""
    notebook_path = os.path.join(PLAYGROUND_DIR, "run.py")
    
    if not os.path.exists(notebook_path):
        print("No run.py found. Skipping execution.")
        return False

    # Convert .py to .ipynb
    notebook_content = f"""# Auto-generated Notebook\n\n```python\n{open(notebook_path).read()}\n```"""
    notebook_file = os.path.join(PLAYGROUND_DIR, "run.ipynb")
    with open(notebook_file, "w") as f:
        f.write(notebook_content)

    # Run the notebook
    print(f"Running notebook: {notebook_file}")
    with open(notebook_file, "r") as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")

    try:
        ep.preprocess(nb, {"metadata": {"path": PLAYGROUND_DIR}})
        with open(notebook_file, "w") as f:
            nbformat.write(nb, f)
        print("Notebook execution completed successfully.")
        return True
    except Exception as e:
        print(f"Notebook execution failed: {e}")
        return False

def clean_up():
    """Deletes everything in the playground folder except run.py"""
    print("Cleaning up playground folder...")
    for file in os.listdir(PLAYGROUND_DIR):
        file_path = os.path.join(PLAYGROUND_DIR, file)
        if file != "run.py":
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

def move_run_script():
    """Moves run.py to results/ and renames it"""
    run_script_path = os.path.join(PLAYGROUND_DIR, "run.py")

    if os.path.exists(run_script_path):
        new_name = input("Enter new name for run.py (without extension): ") + ".py"
        new_path = os.path.join(RESULTS_DIR, new_name)
        
        shutil.move(run_script_path, new_path)
        print(f"Moved run.py to {new_path}")
        return new_path
    return None

def push_results():
    """Commits and pushes changes to GitHub"""
    print("Pushing changes to GitHub...")
    subprocess.run(["git", "add", "."], cwd=REPO_DIR)
    subprocess.run(["git", "commit", "-m", "Processed and updated run.py"], cwd=REPO_DIR)
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
                renamed_file = move_run_script()
                if renamed_file:
                    push_results()  # Push changes only if something was processed
            
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    check_for_changes()
