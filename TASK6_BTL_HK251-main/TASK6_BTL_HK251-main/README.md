 Symbolic and Algebraic Reasoning in Petri Nets 

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

## Installing

- Tải python phiên bản 3.11 (hoặc 3.10) cho window 64 bit
> Lưu ý: nhớ tích chọn thêm PATH cho python khi cài đặt
```
https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
```

- Tải graphviz để tạo hình ảnh (phiên bản 14.0.5 cho window 64bit)
> Lưu ý: nhớ tích chọn thêm PATH cho graphviz khi cài đặt
```
https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/14.0.5/windows_10_cmake_Release_graphviz-install-14.0.5-win64.exe
```

## Requirements

- Tạo môi trường ảo (virtual environment)
```sh
python3 -m venv venv
```
> Nếu không chạy được thì chạy lệnh sau
```sh
py -m venv venv
```
> Nếu máy có nhiều phiên bản python, chạy lệnh
```sh
py -3.11 -m venv venv
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

## Chạy Code

```sh
py run.py
```

##  Chạy tests

- Chạy tất cả các tests
```sh
py -m pytest tests/ -v
```

- Chạy một file test

```sh
py -m pytest tests/test_petriNet.py -v
```

- Chạy một testcase

```sh
py -m pytest tests/test_petriNet.py::test_001 -v
```
