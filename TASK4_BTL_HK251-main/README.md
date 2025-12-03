# TASK 4 – Phát hiện deadlock bằng BDD & ILP

Thư mục này kế thừa **Task 1** (parser PNML & cấu trúc dữ liệu Petri net) và **Task 3** (bao trùm không gian reachable bằng BDD) để tạo thành chu trình đầy đủ phát hiện deadlock reachable trên mạng Petri 1-safe. Bạn có thể tái sử dụng parser của Task 1 để tạo `PetriNet`, chạy qua `bdd_reachable` ở Task 3 và kết hợp với bài toán quy hoạch tuyến tính nguyên để tìm marking bế tắc cụ thể.

## Thành phần thư mục
- `PetriNet.py`: lớp dữ liệu gọn nhẹ lưu thông tin place/transition cùng ma trận `I`, `O` và vector khởi tạo `M0`.
- `BDD.py`: BFS tường minh trên không gian marking reachable rồi chuyển sang BDD (`pyeda`) để biểu diễn tập trạng thái một cách biểu tượng.
- `DeadlockILP.py`: 
  - **Phương pháp ILP**: xây dựng ràng buộc ILP bằng `pulp` nhằm vô hiệu hóa mọi transition; dùng BDD để giữ lại các marking reachable và cắt bỏ nghiệm không hợp lệ.
  - **Phương pháp Enumeration**: enumerate tất cả satisfying assignments từ BDD và kiểm tra từng marking xem có phải dead marking không (không cần `pulp`).
- `test_DeadlockILP.py`: các kịch bản pytest bao gồm mạng có deadlock và không deadlock, bao gồm cả test cases từ TASK4_BTL.
- `requirements.txt`: danh sách phụ thuộc dùng chung (`numpy`, `pyeda`, `pulp`, `pytest`).

## Môi trường & phụ thuộc
- Ưu tiên Python **3.10 hoặc 3.11** vì `pyeda` chưa hỗ trợ tốt 3.12 trở lên.
- Người dùng Windows có thể cần cài **Visual Studio Build Tools** (Desktop development with C++) trước khi cài `pyeda`.

```powershell
# (Tuỳ chọn) xoá venv không tương thích
Remove-Item -Recurse -Force venv

# Tạo và kích hoạt môi trường mới (PowerShell)
py -3.11 -m venv venv
venv\Scripts\Activate.ps1

# Cài các phụ thuộc cần thiết
pip install -r requirements.txt
```

## Chạy kiểm thử
```powershell
py -m pytest test_Deadlock.py -vv
```
Dùng `-k <pattern>` hoặc tên test đầy đủ (ví dụ `py -m pytest test_Deadlock.py -vv -k deadlock`) để chạy case cụ thể.

## Quy trình tìm deadlock

### Phương pháp 1: Sử dụng ILP (khuyến nghị cho mạng lớn)
```python
import numpy as np
from PetriNet import PetriNet
from DeadlockILP import find_deadlock_with_bdd

P = ["p1", "p2"]
T = ["t1"]
I = np.array([[1, 0]])
O = np.array([[0, 1]])
M0 = np.array([1, 0])

pn = PetriNet(P, T, P, T, I, O, M0)
has_deadlock, marking = find_deadlock_with_bdd(pn)

if has_deadlock:
    print("Dead marking:", marking)
else:
    print("Mạng không deadlock trong miền reachable")
```
- `bdd_reachable` (trong `BDD.py`) liệt kê toàn bộ marking 1-safe reachable và trả về cả BDD lẫn số trạng thái.
- `find_deadlock_with_bdd` dựng ILP với biến nhị phân biểu diễn token, đối chiếu nghiệm với BDD và thêm cut cho các marking không reachable cho đến khi tìm được deadlock hoặc ILP vô nghiệm.

### Phương pháp 2: Enumeration (đơn giản hơn, không cần pulp)
```python
import numpy as np
from pyeda.inter import *
from PetriNet import PetriNet
from BDD import bdd_reachable
from DeadlockILP import deadlock_reachable_marking

P = ["p1", "p2"]
T = ["t1"]
I = np.array([[1, 0]])
O = np.array([[0, 1]])
M0 = np.array([1, 0])

pn = PetriNet(P, T, P, T, I, O, M0)
bdd, count = bdd_reachable(pn)
marking = deadlock_reachable_marking(pn, bdd)

if marking is not None:
    print("Dead marking:", marking)
else:
    print("Mạng không deadlock trong miền reachable")
```
- `deadlock_reachable_marking` enumerate tất cả satisfying assignments từ BDD và kiểm tra từng marking xem có phải dead marking không.
- Phương pháp này đơn giản hơn nhưng có thể chậm hơn với mạng có nhiều reachable markings.

## So sánh hai phương pháp

| Đặc điểm | ILP (`find_deadlock_with_bdd`) | Enumeration (`deadlock_reachable_marking`) |
|----------|-------------------------------|-------------------------------------------|
| Độ phức tạp | O(2^n) worst case nhưng thường nhanh hơn | O(2^n) - enumerate tất cả markings |
| Phụ thuộc | Cần `pulp` | Chỉ cần `pyeda` |
| Phù hợp | Mạng lớn, ít reachable markings | Mạng nhỏ, cần implementation đơn giản |
| Trả về | `(bool, Optional[np.ndarray])` | `Optional[List[int]]` |

## Gợi ý
- Khi import PNML, hãy tận dụng parser trong `TASK1_BTL_HK251-main` để khỏi dựng ma trận thủ công.
- Có thể tái sử dụng các tiện ích BDD ở Task 3 nếu bạn cần thêm thống kê hoặc trực quan trước khi sang bước ILP.
- Mở rộng `test_DeadlockILP.py` bằng những mạng tự thiết kế để kiểm tra các trường hợp như self-loop hoặc transition song song.
- Test cases từ `TASK4_BTL_HK251-main` đã được tích hợp vào `test_DeadlockILP.py` (test_001 đến test_006).
