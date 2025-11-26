# TASK 3 BTL MHHHH

**Binary Decision Diagrams (BDDs)

**Every commands listed here can be prompted into any terminal

## Running step by step


Step 0: Install "Pyeda" libary
Preferbly Python version of 3.11 or 3.10, since using "pyeda" library
And also download Visual Studio Build Tools (if u dont have 1):
```
https://visualstudio.microsoft.com/fr/visual-cpp-build-tools/
```
If it's above 3.11, then try to download another Python with version 3.11
If done -> install pyeda with the below command:
```
pip install pyeda
```


(Skip this step if there is no venv file in your main OR you already know to remove the current venv file)

Due to the limitation of pyeda library, the python has to be in version 3.11 or below inorder to get the best result.
Therefore, there will be somecases where you accidentally cooked your self with the 3.12+ version of venv file
Step 0.5: 
If there is an existed venv file in your main and you cannot cook your following step
-> Then try to remove it by these following commands:
```
deactivate
```
&
```
Remove-Item -Recurse -Force venv
```
(To check if there are any remain)
```
dir
```


Step 1: Create environment:
```
py -m venv venv
```
In case you have multiple versions of Python:
```
py -3.11 -m venv venv
```

Step 2: Activate environment:
```
# Windows
venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

Step 3: Install every neccesary libraries from requirement.txt:
(Check the requirement.txt, it has to be: pyeda>=0.29.0)
```
pip install -r requirements.txt
```


##  Running tests

- Run all tests
```
py -m pytest test_BDD.py -vv
```

- Run a single test function

```
py -m pytest test_BDD.py -vv test_BDD.py::test_001
```
