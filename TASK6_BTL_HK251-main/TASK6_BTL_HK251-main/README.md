 Symbolic and Algebraic Reasoning in Petri Nets 

```mermaid
flowchart TD
    %% Nút Bắt đầu và Kết thúc (Hình elip)
    START([START])
    END([END])

    %% Các Task (Hình chữ nhật)
    TASK1{TASK 1: PNML parsing}
    TASK2{TASK 2: Explicit reachability}
    TASK3{TASK 3: BDD-based reachability}
    TASK4{TASK 4: ILP + BDD deadlock detection}
    TASK5{TASK 5: Reachable optimization}

    %% Định nghĩa luồng công việc
    START --> TASK1

    %% Từ TASK 1 chia thành 2 nhánh chính
    TASK1 --> TASK2
    TASK1 --> TASK3

    %% TASK 2 kết thúc
    TASK2 --> END

    %% Từ TASK 3 chia thành 2 nhánh phụ
    TASK3 --> TASK4
    TASK3 --> TASK5

    %% TASK 4 và TASK 5 kết thúc
    TASK4 --> END
    TASK5 --> END

    %% Đặt lại màu sắc (Tùy chọn, cần Mermaid hỗ trợ styling)
    style START fill:#c1e1c1, stroke:#468847, stroke-width:2px
    style END fill:#c1e1c1, stroke:#468847, stroke-width:2px
    style TASK1 fill:#f2baba, stroke:#a94442, stroke-width:2px
    style TASK2 fill:#d8bfd8, stroke:#800080, stroke-width:2px
    style TASK3 fill:#add8e6, stroke:#31708f, stroke-width:2px
    style TASK4 fill:#ffebcd, stroke:#ffc107, stroke-width:2px
    style TASK5 fill:#00ced1, stroke:#008b8b, stroke-width:2px
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
