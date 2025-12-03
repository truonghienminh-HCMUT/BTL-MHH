from collections import deque
import numpy as np
from .PetriNet import PetriNet
from typing import Set, Tuple

def bfs_reachable(pn: PetriNet) -> Set[Tuple[int, ...]]:
    """
    Thuật toán tìm kiếm theo chiều rộng (BFS) để liệt kê không gian trạng thái.
    Sử dụng Hàng đợi (Queue) - Cơ chế FIFO (Vào trước ra trước).
    """
    
    # 1. Chuẩn bị trạng thái ban đầu (M0)
    # Chuyển từ numpy array sang tuple số nguyên (int) để có thể dùng làm key trong set (hashable)
    # Việc map(int, ...) giúp tránh lỗi so sánh giữa numpy.int64 và int thường của Python
    initial_m = tuple(map(int, pn.M0))
    
    # Số lượng place (dựa vào độ dài vector marking)
    num_places = len(initial_m)
    
    # 2. Khởi tạo cấu trúc dữ liệu cho BFS
    # queue: Hàng đợi chứa các marking đang chờ duyệt
    # visited: Tập hợp (Set) lưu các marking đã duyệt để tránh vòng lặp vô tận
    queue = deque([initial_m])
    visited = {initial_m}
    
    # 3. Xử lý sự không nhất quán về kích thước ma trận trong Testcase
    # Lấy kích thước dòng và cột của ma trận Input (I)
    rows, cols = pn.I.shape
    
    # Mặc định theo lý thuyết Petri Net: Số dòng = Số Place (P x T)
    is_standard_shape = True 
    num_transitions = cols
    
    # Kiểm tra: Nếu số dòng KHÁC số place, nhưng số cột lại BẰNG số place
    # => Dữ liệu test đang viết ma trận theo dạng (Transition x Place) thay vì chuẩn
    if rows != num_places and cols == num_places:
        is_standard_shape = False
        num_transitions = rows # Lúc này số transition là số dòng
    
    # 4. Vòng lặp chính duyệt không gian trạng thái
    while queue:
        # Lấy trạng thái hiện tại ra khỏi đầu hàng đợi (FIFO)
        current_m_tuple = queue.popleft()
        current_m_arr = np.array(current_m_tuple)
        
        # Duyệt qua tất cả các transition (sự kiện) trong hệ thống
        for t in range(num_transitions):
            
            # Lấy vector Input (điều kiện bắn) và Output (kết quả bắn) của transition t
            if is_standard_shape:
                # Trường hợp chuẩn: Mỗi cột là một transition
                in_vec = pn.I[:, t]
                out_vec = pn.O[:, t]
            else:
                # Trường hợp Testcase bị xoay: Mỗi dòng là một transition (như Test 004, 005)
                in_vec = pn.I[t, :]
                out_vec = pn.O[t, :]
            
            # 5. Kiểm tra điều kiện bắn (Firing Rule)
            # Transition t chỉ bắn được nếu Marking hiện tại chứa đủ token yêu cầu (M >= I)
            if np.all(current_m_arr >= in_vec):
                
                # Tính toán trạng thái mới: M' = M - Input + Output
                next_m_arr = current_m_arr - in_vec + out_vec
                
                # 6. Kiểm tra thuộc tính 1-safe (Quan trọng)
                # Bài toán yêu cầu 1-safe Petri net, tức là mỗi place chỉ chứa tối đa 1 token.
                # Nếu trạng thái mới có place nào chứa > 1 token, ta bỏ qua trạng thái đó.
                if np.any(next_m_arr > 1):
                    continue
                
                # Chuyển đổi trạng thái mới về dạng tuple chuẩn để lưu trữ
                next_m_tuple = tuple(map(int, next_m_arr))
                
                # Nếu trạng thái này chưa từng xuất hiện, thêm vào danh sách duyệt
                if next_m_tuple not in visited:
                    visited.add(next_m_tuple)
                    queue.append(next_m_tuple)
                    
    # Trả về tập hợp tất cả các marking tìm thấy
    return visited