# TASK 5 BTL MÔ HÌNH TOÁN HÓA HỌC

**Optimization over reachable markings:** Given a linear objective function
maximize c⊤M, M ∈Reach(M0),
where Reach(M0) denotes the set of markings reachable from the initial marking M0 and c
assigns integer weights to places, determine a reachable marking if it exists that optimizes
the objective function. If there is no such a marking, report none. Report the running
time on some example models.

## Before running

- Install Python version 3.10.x or 3.11.x
```
https://www.python.org/downloads/release/python-3119/
```
Here is Python 3.11.9, please remember to check on create path

- Set virtual environment
```
# Use this when you have more than 1 version of Python
py -3.11 -m venv venv
```
Or
```
py -m venv venv
```

- Activate virtual environment
```
# For Windows
venv\Scripts\Activate.ps1

# For Linux / macOS:
source venv/bin/activate
```

- Install some libraries from `requirements.txt`
```
pip install -r requirements.txt
```

- If you have some problems by install Pyeda, run this command first
```
pip install pyeda
```

##  Running tests

- Run all tests
```
python -m pytest -vv test_Optimization.py
```

- Run a single test function

```
python -m pytest -vv test_Optimization.py::test_001
```

## Delete

- Run this two command
```
deactivate
```
and
```
Remove-Item -Recurse -Force venv
```