 Symbolic and Algebraic Reasoning in Petri Nets 

**Này thiết kế src của anh các bạn có thể chỉnh lại src theo cấu trúc nhóm mình cho khác đi khỏi bị trùng cấu trúc**

```mermaid
flowchart TD

    %% Places
    P1(("TASK1"))
    P4(("TASK4"))
    P5(("TASK5"))

    %% Transitions
    P23([TASK2 & TASK3])

    %% Arcs 
    P1 --> P23
    P23 --> P4
    P4 --> P5
```

## Requirements

- Tạo môi trường ảo (virtual environment)
```sh
python3 -m venv venv
```
> Nếu không chạy được thì chạy lệnh sau
```sh
python -m venv venv
```
> Nếu máy có nhiều phiên bản python, chạy lệnh
```sh
python -3.11 -m venv venv
```


- Kích hoạt môi trường ảo
```sh
# Windows
venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

- Cài đặt các thư viện từ `requirements.txt`
```sh
pip install -r requirements.txt
```

## Running Code

```sh
python3 run.py
```

##  Running tests

- Run all tests
```sh
python3 -m pytest tests/ -v
```

- Run a single test FIle

```sh
python3 -m pytest tests/test_petriNet.py -v
```

- Run a single test FIle

```sh
python3 -m pytest tests/test_petriNet.py::test_001 -v
```
