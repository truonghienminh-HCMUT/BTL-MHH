import collections
from typing import Tuple, List, Optional
from pyeda.inter import *
from collections import deque
import numpy as np

def max_reachable_marking(
    place_ids: List[str], 
    bdd: BinaryDecisionDiagram, 
    c: np.ndarray
) -> Tuple[Optional[List[int]], Optional[int]]:
    """
    Tìm marking M trong tập reachable (biểu diễn bởi bdd) sao cho c^T * M là lớn nhất.
    """
    
    # 1. Kiểm tra BDD rỗng
    if bdd.is_zero():
        return None, None

    n = len(place_ids)
    
    # Mapping từ tên biến BDD sang index của vector trọng số c
    var_name_to_index = {name: i for i, name in enumerate(place_ids)}
    
    # Memoization: Key=Node, Value=(max_val, choice)
    memo = {}

    def get_var_index(node) -> int:
        """Helper để lấy index của biến tại node BDD."""
        # node.top trả về đối tượng biến (Variable). 
        # str(node.top) sẽ trả về tên biến (ví dụ "p1" hoặc "x[0]")
        var_name = str(node.top)
        
        if var_name in var_name_to_index:
            return var_name_to_index[var_name]
        
        # Trường hợp biến BDD không khớp tên trong place_ids
        raise ValueError(f"Biến BDD '{var_name}' không tìm thấy trong place_ids: {place_ids}")

    def get_skipped_gain(start_idx: int, end_idx: int) -> int:
        """Tính tổng trọng số dương của các biến bị nhảy qua (Don't care variables)."""
        gain = 0
        for i in range(start_idx, end_idx):
            if c[i] > 0:
                gain += c[i]
        return gain

    def solve(node) -> Tuple[float, int]:
        """
        Trả về (Giá trị lớn nhất từ node này, Hướng đi tốt nhất)
        """
        # Base case: Terminal 1 -> Thành công (đến đích)
        if node.is_one():
            return 0.0, -1 
        
        # Base case: Terminal 0 -> Thất bại (đường cụt)
        if node.is_zero():
            return float('-inf'), -1

        if node in memo:
            return memo[node]

        # Lấy biến tại node hiện tại
        top_var = node.top
        curr_idx = get_var_index(node)

        # --- Nhánh LOW (x = 0) ---
        # Sử dụng restrict để lấy node con tương ứng với gán x=0
        low_node = node.restrict({top_var: 0})
        low_val, _ = solve(low_node)
        
        total_low = float('-inf')
        if low_val != float('-inf'):
            # Xác định index của node con để tính skip
            if low_node.is_one() or low_node.is_zero():
                next_idx_low = n
            else:
                next_idx_low = get_var_index(low_node)
                
            skipped_gain = get_skipped_gain(curr_idx + 1, next_idx_low)
            total_low = low_val + skipped_gain

        # --- Nhánh HIGH (x = 1) ---
        # Sử dụng restrict để lấy node con tương ứng với gán x=1
        high_node = node.restrict({top_var: 1})
        high_val, _ = solve(high_node)
        
        total_high = float('-inf')
        if high_val != float('-inf'):
            # Xác định index node con
            if high_node.is_one() or high_node.is_zero():
                next_idx_high = n
            else:
                next_idx_high = get_var_index(high_node)
                
            skipped_gain = get_skipped_gain(curr_idx + 1, next_idx_high)
            # Cộng thêm trọng số của chính node hiện tại (vì chọn x=1)
            total_high = high_val + skipped_gain + c[curr_idx]

        # --- So sánh và lưu kết quả ---
        if total_high >= total_low:
            res = (total_high, 1) # 1: Chọn nhánh High
        else:
            res = (total_low, 0)  # 0: Chọn nhánh Low
            
        memo[node] = res
        return res

    # --- Bước 1: Tính giá trị max (Bottom-up DP) ---
    root_val, _ = solve(bdd)

    if root_val == float('-inf'):
        return None, None

    # --- Bước 2: Dựng lại Marking (Top-down Reconstruction) ---
    final_marking = [0] * n
    
    # Xử lý các biến bị skip TRƯỚC root (nếu có)
    if bdd.is_one():
        root_idx = n
    else:
        root_idx = get_var_index(bdd)
        
    for i in range(0, root_idx):
        if c[i] > 0: final_marking[i] = 1

    # Duyệt từ root xuống terminal 1 dựa trên choice trong memo
    curr_node = bdd
    while not curr_node.is_one():
        curr_idx = get_var_index(curr_node)
        top_var = curr_node.top
        
        # Lấy choice đã lưu
        if curr_node not in memo:
            break # Should not happen
        max_val, choice = memo[curr_node]
        
        # Gán giá trị cho biến tại node hiện tại
        final_marking[curr_idx] = choice
        
        # Di chuyển xuống node con tương ứng
        if choice == 1:
            next_node = curr_node.restrict({top_var: 1})
        else:
            next_node = curr_node.restrict({top_var: 0})
            
        # Xử lý biến bị skip giữa node hiện tại và node kế tiếp
        if next_node.is_one() or next_node.is_zero():
            next_idx = n
        else:
            next_idx = get_var_index(next_node)
            
        for i in range(curr_idx + 1, next_idx):
            if c[i] > 0: final_marking[i] = 1
            else: final_marking[i] = 0
            
        curr_node = next_node

    # Cộng thêm giá trị skip trước root vào tổng cuối cùng
    pre_root_gain = get_skipped_gain(0, root_idx)
    final_total_value = root_val + pre_root_gain

    return final_marking, int(final_total_value)
