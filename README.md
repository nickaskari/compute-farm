# compute-farm
Compute Automation NTNU - Finanssal

1. But files inside the folder of the machine you want to run. I.E machine_1. The folder should have a notebook called run.ipynb, this is what will be ran.
2. If you have extra requirements, before pushing your code. Bring the requirements of your project to root folder, call it requirements_2.txt and run r_merger.ipynb first.
3. If you are a Machine, create a .env.local file and spesify MACHINE_NUMBER = X.

## Usefull comands


```sh
python -m venv packages 
```

```sh
.\packages\Scripts\activate
```

```sh
pip freeze > requirements.txt
```
Installing all libraries from requirements.txt,
```sh
pip install -r requirements.txt
```
