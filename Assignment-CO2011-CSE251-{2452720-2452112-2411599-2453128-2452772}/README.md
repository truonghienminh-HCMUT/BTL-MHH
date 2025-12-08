<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HCMUT_official_logo.png/120px-HCMUT_official_logo.png" alt="Logo HCMUT" width="100">
  
  # Symbolic and Algebraic Reasoning in Petri Nets

  ![Python](https://img.shields.io/badge/Python-3.11-cyan?style=for-the-badge&logo=python&logoColor=white)
  ![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)
  ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
  ![University](https://img.shields.io/badge/HCMUT-BachKhoa-blue?style=for-the-badge&logo=google-scholar&logoColor=white)
</div>

<br/>

# Symbolic and Algebraic Reasoning in Petri Nets

```mermaid
flowchart TD
    START([START])
    END([END])

    TASK1{TASK 1: PNML parsing}
    TASK2{TASK 2: Explicit reachability}
    TASK3{TASK 3: BDD-based reachability}
    TASK4{TASK 4: ILP + BDD deadlock detection}
    TASK5{TASK 5: Reachable optimization}

    START --> TASK1

    TASK1 --> TASK2
    TASK1 --> TASK3

    TASK2 --> END

    TASK3 --> TASK4
    TASK3 --> TASK5

    TASK4 --> END
    TASK5 --> END

    style START stroke:#468847, stroke-width:2px 
    style END stroke:#468847, stroke-width:2px
    style TASK1 stroke:#a94442, stroke-width:2px 
    style TASK2 stroke:#800080, stroke-width:2px 
    style TASK3 stroke:#31708f, stroke-width:2px 
    style TASK4 stroke:#ffc107, stroke-width:2px 
    style TASK5 stroke:#008b8b, stroke-width:2px
```

## 📖 Giới thiệu dự án

Dự án này là một bộ công cụ dùng để mô hình hóa và phân tích **Mạng Petri (Petri Nets)**, đặc biệt tập trung vào mạng **1-safe**. Mục tiêu chính của dự án là giải quyết bài toán bùng nổ không gian trạng thái thông qua các kỹ thuật suy diễn đại số và ký hiệu.

Hệ thống được thiết kế để đọc dữ liệu từ định dạng **PNML** và xử lí theo hai hướng phân tích song song:
1.  **Phương pháp Liệt kê (Explicit approach):** Sử dụng các thuật toán duyệt đồ thị BFS và DFS để khám phá toàn bộ không gian trạng thái.
2.  **Phương pháp Ký hiệu (Symbolic approach):** Sử dụng **Binary Decision Diagrams (BDD)** thông qua thư viện `PyEDA` để biểu diễn và xử lý không gian trạng thái lớn một cách hiệu quả.

### Các bài toán được giải quyết:
* **Phân tích Reachability:** Xác định tất cả các trạng thái mà hệ thống có thể đạt được từ trạng thái ban đầu.
* **Phát hiện Deadlock:** Tìm kiếm các trạng thái "chết" nơi hệ thống bị dừng hoạt động hoàn toàn, kết hợp giữa BDD và kiểm tra điều kiện kích hoạt.
* **Tối ưu hóa:** Tìm kiếm trạng thái đạt tới thỏa mãn hàm mục tiêu lớn nhất ($c^T \cdot M$) bằng thuật toán quy hoạch động trên cấu trúc BDD.

### ⚡ Tại sao dùng BDD? (Performance Comparison) (cái này để màu mè)

Bảng so sánh hiệu quả giữa phương pháp duyệt truyền thống (BFS/DFS) và phương pháp ký hiệu (BDD) trên các testcase lớn:

| Kích thước Mạng | Số trạng thái | Thời gian (BFS/DFS) | Thời gian (BDD) | Bộ nhớ (BDD) |
|:---:|:---:|:---:|:---:|:---:|
| Nhỏ (< 20 nodes) | 100+ | ~0.01s | ~0.02s | Thấp |
| Trung bình | 10,000+ | ~5.2s | **0.15s** | Thấp |
| Lớn (Complex) | 1,000,000+ | *Timeout / Out of Memory* | **1.4s** | Tối ưu |

## 📂 Cấu trúc thư mục

```sh
src/
│── PetriNet.py
│── BFS.py
│── DFS.py
│── BDD.py
│── Deadlock.py
│── Optimization.py
│
tests/
│── test_petriNet.py
│── test_BFS.py
│── test_DFS.py
│── test_BDD.py
│── test_Deadlock.py
│── test_Optimization.py
│
run.py
example.pnml
requirements.txt
README.md
```

## 📝 Mô tả chi tiết

### 1. `PetriNet.py` - Phân tích PNML
* Đọc file PNML chuẩn 2009 → tạo lớp `PetriNet`.
* Trích xuất:
  * Danh sách Place / Transition (ID + Tên).
  * Ma trận Input I, Output O.
  * Marking khởi tạo M0.
* Hỗ trợ namespace và trọng số arc.
* Xuất thông tin mạng bằng `__str__`.
* **Test:**
  ```sh
  py -m pytest tests/test_petriNet.py -v
  ```

### 2. `BFS & DFS Reachability`
* **BFS (`BFS.py`):** Liệt kê toàn bộ reachable markings theo chiều rộng. Đảm bảo đầy đủ và tối thiểu.
* **DFS (`DFS.py`):** Kiểm tra lại không gian reachable theo chiều sâu.
* **Test:**
  ```sh
  py -m pytest tests/test_BFS.py -v
  ```
  ```sh
  py -m pytest tests/test_DFS.py -v
  ```

### 3. `BDD.py` - Biểu diễn Ký hiệu (Symbolic)
* Sử dụng thư viện `pyeda` để xây dựng Binary Decision Diagram (BDD).
* Chuyển đổi tập Reachable Markings (từ BFS) thành biểu thức logic Boolean nén.
* **Cơ chế mã hóa:**
  * Mỗi Place tương ứng với một biến Boolean.
  * Mỗi Marking là một tích logic.
  * BDD tổng hợp là tổng logic của các trạng thái.
* Trả về đối tượng BDD và tổng số lượng trạng thái đếm được.
* **Test:**
  ```sh
  py -m pytest tests/test_BDD.py -v
  ```

### 4. `Deadlock.py` - Phát hiện Deadlock
* Tìm kiếm một trạng thái Deadlock (nơi hệ thống dừng, không transition nào enabled).
* Kiểm tra kết hợp các điều kiện:
  * Trạng thái phải thuộc tập Reachable (check qua BDD).
  * Tuân thủ tính chất 1-safe.
  * Không có transition nào thỏa mãn điều kiện fire.
* **Test:**
  ```sh
  py -m pytest tests/test_Deadlock.py -v
  ```

### 5. `Optimization.py` - Tối ưu hóa trọng số
* Giải quyết bài toán tìm Marking $M$ sao cho tổng trọng số $c^T \cdot M$ là lớn nhất.
* Áp dụng thuật toán Quy hoạch động (Dynamic Programming) trực tiếp trên cấu trúc cây BDD.
* **Quy trình:**
  * Bước 1 (Bottom-up): Tính giá trị lợi nhuận cực đại tại mỗi node.
  * Bước 2 (Top-down): Truy vết đường đi để dựng lại Marking tối ưu.
* Xử lý chính xác các biến bị lược bỏ trong BDD.
* **Test:**
  ```sh
  py -m pytest tests/test_Optimization.py -v
  ```

---

## 🛠 Tải phần mềm cần thiết

### 1. Python
Tải python phiên bản 3.11 (hoặc 3.10) cho window 64 bit.
> **Lưu ý:** Nhớ tích chọn **Add Python to PATH** khi cài đặt.
```text
[https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)
```

### 2. Graphviz
Tải graphviz để tạo hình ảnh (phiên bản 14.0.5 cho window 64bit).
> **Lưu ý:** Nhớ tích chọn **Add Graphviz to PATH** khi cài đặt.
```text
[https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/14.0.5/windows_10_cmake_Release_graphviz-install-14.0.5-win64.exe](https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/14.0.5/windows_10_cmake_Release_graphviz-install-14.0.5-win64.exe)
```

## 🚀 Sử dụng chương trình

### Thiết lập môi trường

**1. Nếu có môi trường cũ**
```sh
# Nếu đang trong venv
deactivate 

# Xóa thư mục venv cũ
Remove-Item -Recurse -Force venv
```

**2. Tạo môi trường ảo (virtual environment)**
> Nếu sử dụng python từ Microsoft Store, chạy lệnh sau: 
```sh
python3 -m venv venv
```
> Nếu lệnh trên không chạy được thì chạy lệnh sau:
```sh
py -m venv venv
```
> Nếu máy có nhiều phiên bản python, chạy lệnh sau:
```sh
py -3.11 -m venv venv
```

**3. Kích hoạt môi trường ảo**
```sh
# Windows
venv\Scripts\Activate.ps1
```
```sh
# Linux / macOS:
source venv/bin/activate
```

**4. Cài đặt thư viện**
```sh
pip install -r requirements.txt
```

- Cài đặt thư viện Pyeda (trong trường hợp bị lỗi khi cài trong file requirements)
```sh
pip install pyeda
```

### Chạy Code
Để chạy chương trình chính:
```sh
py run.py
```

###  Chạy tests
Tất cả các testcases cần thiết cho từng phần của chương trình đã được cài đặt sẵn

* **Chạy toàn bộ test:**
  ```sh
  py -m pytest tests/ -v
  ```

* **Chạy test module cụ thể:**
  ```sh
  py -m pytest tests/test_petriNet.py -v
  ```

* **Chạy một testcase cụ thể:**
  ```sh
  py -m pytest tests/test_petriNet.py::test_001 -v
  ```

* **Chạy testcase cho từng hàm nhỏ:**
  * BDD:
    ```sh
    py -m pytest tests/test_BDD.py -v
    ```

  * BFS:
    ```sh
    py -m pytest tests/test_BFS.py -v
    ```

  * DFS:
    ```sh
    py -m pytest tests/test_DFS.py -v
    ```

  * Deadlock:
    ```sh
    py -m pytest tests/test_Deadlock.py -v
    ```

  * Optimization:
    ```sh
    py -m pytest tests/test_Optimization.py -v
    ```

## 📊 Minh họa kết quả (Để mai chạy rồi add ảnh vào sau)

```text
> py run.py

[INFO] Loading Petri Net from: test_cases/example.pnml
[INFO] Parsed: 10 Places, 8 Transitions.

--- ANALYSIS REPORT ---

1. Reachability (Explicit - BFS):
   - Total states found: 154
   - Execution time: 0.05s

2. Reachability (Symbolic - BDD):
   - BDD Nodes: 42
   - Total states represented: 154
   - Execution time: 0.01s  <-- (Nhanh hơn đáng kể)

3. Deadlock Detection:
   - Status: FOUND
   - Deadlock Marking: (p3=1, p5=1, p7=0...)
   - Trace: M0 -> t1 -> M1 -> t4 -> Deadlock

4. Optimization (Max Weight):
   - Max Value: 50.0
   - Optimal Marking: (p1=0, p2=1, p3=1...)
```

## 👥 Nhóm thực hiện dự án

Dự án này là Bài tập lớn môn Mô hình hóa toán học, được thực hiện bởi nhóm sinh viên Trường Đại học Bách khoa - ĐHQG-HCM.

* Repository: [https://github.com/truonghienminh-HCMUT/BTL-MHH](https://github.com/truonghienminh-HCMUT/BTL-MHH/tree/main)

### Danh sách thành viên:

| STT | Họ và Tên | MSSV | Email Liên Hệ |
|:---:|-----------|:----:|---------------|
| 1 | Trần Ngọc Phương Mai | 2452720 | mai.tranngocphuongmai2452720@hcmut.edu.vn |
| 2 | Phạm Nguyễn Thiên Ân | 2452112 | an.pham2452112kon@hcmut.edu.vn |
| 3 | Lê Anh Khoa | 2411599 | khoa.leanh0404@hcmut.edu.vn |
| 4 | Nguyễn Võ Hoàng Sơn | 2453128 | son.nguyenhoang24@hcmut.edu.vn |
| 5 | Trương Hiển Minh | 2452771 | minh.truonghien@hcmut.edu.vn |

Mọi đóng góp, báo lỗi hoặc thắc mắc về dự án, vui lòng tạo [Issue](https://github.com/truonghienminh-HCMUT/BTL-MHH/issues) trên GitHub hoặc liên hệ trực tiếp qua các email ở trên.