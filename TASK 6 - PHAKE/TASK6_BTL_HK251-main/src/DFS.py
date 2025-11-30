from collections import deque
import numpy as np
from .PetriNet import PetriNet
from typing import Set, Tuple

def dfs_reachable(pn: PetriNet) -> Set[Tuple[int, ...]]:
    """
    Thực hiện thuật toán Tìm kiếm theo chiều sâu (DFS) để khám phá không gian trạng thái.
    - Input: Mạng Petri (chứa M0, ma trận Input I, ma trận Output O).
    - Output: Tập hợp tất cả các marking có thể đạt được (Reachable Set).
    """
    
    # 1. Chuẩn hóa trạng thái ban đầu (Initial Marking - M0)
    # Chuyển đổi từ numpy array sang tuple(int) để đảm bảo tính "hashable" (có thể lưu vào set).
    # map(int, ...) giúp loại bỏ sự phụ thuộc vào kiểu dữ liệu numpy.int64.
    initial_m = tuple(map(int, pn.M0))
    
    # Xác định số lượng Place dựa trên độ dài vector marking
    num_places = len(initial_m)
    
    # 2. Khởi tạo cấu trúc dữ liệu cho DFS
    # 'stack': Ngăn xếp lưu các marking chờ duyệt (Cơ chế LIFO - Vào sau ra trước)
    stack = [initial_m]
    
    # 'visited': Tập hợp lưu các marking đã duyệt để tránh vòng lặp vô tận
    visited = {initial_m}
    
    # --- 3. TỰ ĐỘNG PHÁT HIỆN HƯỚNG CỦA MA TRẬN (Matrix Orientation Detection) ---
    # Mục đích: Xử lý trường hợp dữ liệu đầu vào không nhất quán (Testcase lúc thì PxT, lúc thì TxP).
    rows, cols = pn.I.shape
    
    # Giả định mặc định: Cấu trúc chuẩn (Hàng = Place, Cột = Transition)
    is_row_place = True 
    num_transitions = cols
    
    # Logic kiểm tra: Nếu số dòng ma trận KHÁC số lượng Place thực tế, 
    # nhưng số cột lại BẰNG số Place => Ma trận đang bị xoay ngang (Transition x Place).
    if rows != num_places and cols == num_places:
        is_row_place = False
        num_transitions = rows # Lúc này số transition tương ứng với số dòng
    # -----------------------------------------------------------------------------
    
    # 4. Vòng lặp chính duyệt không gian trạng thái
    while stack:
        # Lấy trạng thái từ ĐỈNH ngăn xếp (Pop phần tử mới nhất)
        current_m_tuple = stack.pop()
        
        # Chuyển về dạng numpy array để thực hiện phép toán vector (cộng/trừ ma trận)
        current_m_arr = np.array(current_m_tuple)
        
        # Duyệt qua từng transition để tìm trạng thái kế tiếp
        for t in range(num_transitions):
            
            # Trích xuất vector Input (Pre) và Output (Post) của transition t
            if is_row_place:
                # Trường hợp chuẩn: Lấy dữ liệu theo cột
                in_vec = pn.I[:, t]
                out_vec = pn.O[:, t]
            else:
                # Trường hợp ma trận bị xoay: Lấy dữ liệu theo hàng
                in_vec = pn.I[t, :]
                out_vec = pn.O[t, :]
            
            # 5. Kiểm tra điều kiện bắn (Firing Rule)
            # Transition t chỉ được kích hoạt nếu số token hiện tại >= số token yêu cầu (Input)
            if np.all(current_m_arr >= in_vec):
                
                # Tính toán trạng thái mới theo công thức: M' = M - Input + Output
                next_m_arr = current_m_arr - in_vec + out_vec
                
                # --- 6. KIỂM TRA TÍNH CHẤT 1-SAFE (Quan trọng) ---
                # Bài toán yêu cầu mạng 1-safe (mỗi place tối đa 1 token).
                # Nếu trạng thái mới vi phạm (có place > 1 token) -> Bỏ qua nhánh này.
                if np.any(next_m_arr > 1):
                    continue
                # -------------------------------------------------
                
                # Chuyển trạng thái mới về dạng tuple chuẩn
                next_m_tuple = tuple(map(int, next_m_arr))
                
                # Nếu trạng thái này chưa từng được duyệt
                if next_m_tuple not in visited:
                    # Đánh dấu đã thăm
                    visited.add(next_m_tuple)
                    # Đẩy vào stack để tiếp tục duyệt sâu từ trạng thái này
                    stack.append(next_m_tuple)
                    
    # Trả về toàn bộ tập trạng thái tìm được
    return visited