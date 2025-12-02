# Symbolic and Algebraic Reasoning in Petri Nets 

**Này thiết kế src của anh các bạn có thể chỉnh lại src theo cấu trúc nhóm mình cho khác đi khỏi bị trùng cấu trúc**

```mermaid
flowchart TD

    %% Places
    P1(("TASK1"))
    P2(("TASK2"))
    P3(("TASK3"))
    P4(("TASK4"))
    P5(("TASK5"))

    %% Transitions
    T12([T1_to_T2])
    T13([T1_to_T3])
    T134([T1_T3_to_T4])
    T135([T1_T3_to_T5])

    %% Arcs
    P1 --> T12
    T12 --> P2

    P1 --> T13
    T13 --> P3

    P1 --> T134
    P3 --> T134
    T134 --> P4

    P1 --> T135
    P3 --> T135
    T135 --> P5
```

## Requirements

- Tạo môi trường ảo (virtual environment)
```sh
python3 -m venv venv
```
Nếu không chạy được thì chạy lệnh sau
```sh
python -m venv venv
```
Nếu máy có nhiều phiên bản python, chạy lệnh
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
