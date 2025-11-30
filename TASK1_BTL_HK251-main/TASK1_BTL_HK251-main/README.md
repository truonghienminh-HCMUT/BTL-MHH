# TASK 1 BTL MHH: PNML Parser & Data Structure 

**Reading Petri nets from PNML files**: Xây dựng một module phân tích cú pháp (parser) có khả năng đọc dữ liệu mạng Petri loại 1-safe từ tệp PNML chuẩn. Hệ thống cần thiết lập được cấu trúc dữ liệu nội bộ đại diện cho các vị trí (places), chuyển đổi (transitions) và các quan hệ luồng (flow relations). Đồng thời, chương trình phải thực hiện việc kiểm tra tính toàn vẹn của dữ liệu (ví dụ: xác minh không có nút hay cung nào bị khuyết).

https://www.pnml.org/version-2009/version-2009.php

## 🌟 Tính năng
- Đọc file `.pnml` tiêu chuẩn
- Tự động trích xuất
  - Danh sách Places và Transitions.
  - Ma trận trọng số đầu vào (Input Matrix - I).
  - Ma trận trọng số đầu rqa (Output Matrix - O).
  - Vector trạng thái ban đầu (Initial Marking - MO).   


## 🛠 Yêu cầu hệ thống
- Python 3.x
- Thư viện: `numpy`
- pytest

## 📦 Cài đặt
        1. Clone dự án này về máy:

        2. Cài đặt thư viện cần thiết (nếu chưa có):
        ```
        pip install numpy
        ```

        3. Cài đặt pytest (nếu chưa có):
        ```
        pip install pytest
        ```
        Hoặc nếu dùng Python 3:
        ```
        python -m pip install pytest
        ```


##  Chạy testcase

- Run all tests
```
pytest test_petriNet.py -vv
```

- Run a single test function

```
pytest test_petriNet.py -vv
```

---
