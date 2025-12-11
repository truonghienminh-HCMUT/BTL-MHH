import collections
from typing import Tuple
from pyeda.inter import *
from src.PetriNet import PetriNet
import numpy as np
import time

def reorder_places_bfs(pn: PetriNet) -> list:
    """
    Sắp xếp lại thứ tự biến BDD dựa trên cấu trúc đồ thị (BFS).
    Giúp tối ưu hóa kích thước BDD bằng cách đặt các Place có quan hệ gần nhau nằm cạnh nhau.
    """
    # 1. Xây dựng đồ thị kề (Adjacency Graph) giữa các Place
    adj = collections.defaultdict(set)
    
    if hasattr(pn, "I"): I = np.array(getattr(pn, "I"), dtype=int)
    else: I = np.array(getattr(pn, "pre"), dtype=int)
    
    if hasattr(pn, "O"): O = np.array(getattr(pn, "O"), dtype=int)
    else: O = np.array(getattr(pn, "post"), dtype=int)
    
    # Xác định chiều của ma trận để duyệt đúng Transition
    num_places_obj = len(pn.place_ids)
    r, c = I.shape
    
    # --- FIX: Đồng bộ logic xác định chiều ma trận với hàm chính ---
    if c == num_places_obj: 
        row_is_trans = True # Standard: Hàng là Transition
        num_trans = r
    else:
        row_is_trans = False # Non-standard: Cột là Transition
        num_trans = c

    for t in range(num_trans):
        # Lấy danh sách Input và Output places của transition t
        if row_is_trans:
            inputs = np.where(I[t, :] > 0)[0]
            outputs = np.where(O[t, :] > 0)[0]
        else:
            inputs = np.where(I[:, t] > 0)[0]
            outputs = np.where(O[:, t] > 0)[0]
            
        # Nối tất cả các node liên quan với nhau trong đồ thị vô hướng
        nodes = np.concatenate((inputs, outputs))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                adj[u].add(v)
                adj[v].add(u)

    # 2. Duyệt BFS để tạo thứ tự mới
    visited = [False] * len(pn.place_ids)
    new_order_indices = []
    
    # Duyệt qua tất cả các thành phần liên thông
    for start_node in range(len(pn.place_ids)):
        if not visited[start_node]:
            queue = collections.deque([start_node])
            visited[start_node] = True
            new_order_indices.append(start_node)
            
            while queue:
                u = queue.popleft()
                # Sort neighbors để đảm bảo tính tất định (deterministic)
                neighbors = sorted(list(adj[u]))
                for v in neighbors:
                    if not visited[v]:
                        visited[v] = True
                        new_order_indices.append(v)
                        queue.append(v)
    
    # Trả về danh sách ID theo thứ tự mới
    return [pn.place_ids[i] for i in new_order_indices]

def bdd_reachable(pn: PetriNet) -> Tuple[BinaryDecisionDiagram, int]:
    print("   [BDD] Starting Symbolic Reachability...")
    
    # --- 1. Chuẩn bị dữ liệu Ma trận ---
    if hasattr(pn, "I"): I = np.array(getattr(pn, "I"), dtype=int)
    else: I = np.array(getattr(pn, "pre"), dtype=int)
    
    if hasattr(pn, "O"): O = np.array(getattr(pn, "O"), dtype=int)
    else: O = np.array(getattr(pn, "post"), dtype=int)
    
    if hasattr(pn, "M0"): M0 = np.array(getattr(pn, "M0"), dtype=int).reshape(-1)
    else: M0 = np.array(getattr(pn, "initial_marking"), dtype=int).reshape(-1)

    num_places = M0.shape[0]
    
    # Xác định orientation của ma trận (Hàng là Trans hay Cột là Trans)
    r, c = I.shape
    if c == num_places: 
        row_is_transition = True # Standard: Trans x Place
        num_trans = r
    else: 
        row_is_transition = False # Non-standard: Place x Trans
        num_trans = c

    def get_row_as_vector(matrix, t_idx):
        """Helper lấy vector tương ứng với transition t"""
        return matrix[t_idx, :] if row_is_transition else matrix[:, t_idx]

    # --- 2. Tối ưu hóa thứ tự biến (Variable Reordering) ---
    print("   [BDD] Optimizing variable order (BFS Reordering)...")
    
    # Mapping từ ID cũ sang Index cũ
    old_ids = getattr(pn, "place_ids", [f"p{i}" for i in range(num_places)])
    old_id_to_idx = {pid: i for i, pid in enumerate(old_ids)}
    
    # Lấy thứ tự mới
    new_places_ids = reorder_places_bfs(pn)
    
    # Map lại M0 theo thứ tự mới
    new_M0_list = []
    for pid in new_places_ids:
        old_idx = old_id_to_idx[pid]
        new_M0_list.append(M0[old_idx])
    M0 = np.array(new_M0_list)
    
    # --- 3. Khởi tạo biến BDD ---
    print(f"   [BDD] Creating BDD variables for {num_places} places...")
    # Tạo biến BDD theo thứ tự đã tối ưu
    X_vars = [bddvar(str(p)) for p in new_places_ids]
    
    # --- 4. Tạo Trạng thái Ban đầu (Initial State) ---
    init_lits = []
    for bit, x in zip(M0, X_vars):
        init_lits.append(x if int(bit) == 1 else ~x)
    
    if not init_lits: 
        Reach = bddvar('1')
    else:
        # Tạo biểu thức logic AND cho toàn bộ marking M0
        # M0 = (p1=1) & (p2=0) & ...
        Reach = init_lits[0]
        for lit in init_lits[1:]: 
            Reach = Reach & lit
        
    Frontier = Reach # Tập biên (các trạng thái mới tìm thấy)

    # --- 5. Xây dựng Logic Chuyển đổi (Transition Relations) ---
    print(f"   [BDD] Analyzing {num_trans} transitions...")
    transitions_data = []
    
    # Cần map index ma trận gốc sang index biến BDD mới
    # new_idx_to_old_idx[i] = index trong ma trận gốc của biến BDD thứ i
    new_idx_to_old_idx = [old_id_to_idx[pid] for pid in new_places_ids]
    
    for t in range(num_trans):
        # Lấy vector Pre và Post từ ma trận gốc
        pre_t_raw = get_row_as_vector(I, t)
        post_t_raw = get_row_as_vector(O, t)
        
        # Sắp xếp lại vector theo thứ tự biến BDD
        pre_t = np.array([pre_t_raw[old_idx] for old_idx in new_idx_to_old_idx])
        post_t = np.array([post_t_raw[old_idx] for old_idx in new_idx_to_old_idx])
        
        # Tìm các index (trong hệ qui chiếu mới) có tham gia vào transition
        idx_inputs = set(np.where(pre_t > 0)[0])
        idx_outputs = set(np.where(post_t > 0)[0])
        
        # --- A. Xây dựng điều kiện Enable (Enable Condition) ---
        # Transition t bắn được nếu:
        # 1. Input places có token (p=1)
        # 2. Output places (mà không phải input) KHÔNG có token (p=0) -> 1-safe property
        pre_cond = []
        
        # Ràng buộc Input: p=1
        for idx in idx_inputs: 
            pre_cond.append(X_vars[idx])
            
        # Ràng buộc Output (Contact-free): p=0 (chỉ áp dụng nếu p không phải là input)
        for idx in idx_outputs:
            if idx in idx_inputs: # Nếu không phải self-loop
                continue
            else:
                pre_cond.append(~X_vars[idx])
        
        if not pre_cond: 
            En_Expr = bddvar('1') # Luôn enable (transition source)
        else:
            En_Expr = pre_cond[0]
            for l in pre_cond[1:]: En_Expr &= l

        # --- B. Xây dựng Logic Cập nhật (Update Logic) ---
        # Phương pháp: "Local Transition Relation"
        # 1. Smoothing: Xóa giá trị cũ của các biến thay đổi (exists x)
        # 2. Conjunction: Gán giá trị mới cho các biến đó
        
        vars_involved = idx_inputs.union(idx_outputs) # Tập biến thay đổi
        vars_to_smooth = [X_vars[i] for i in vars_involved]
        
        update_lits = []
        for idx in vars_involved:
            if idx in idx_outputs:
                # Nếu là output -> Token mới sinh ra -> Giá trị = 1
                # (Kể cả self-loop: Input lấy đi, Output trả lại -> Kết quả là 1)
                update_lits.append(X_vars[idx])
            elif idx in idx_inputs:
                # Nếu là input (và không phải output) -> Token bị lấy đi -> Giá trị = 0
                update_lits.append(~X_vars[idx])
            
        if not update_lits: 
            Up_Expr = bddvar('1')
        else:
            Up_Expr = update_lits[0]
            for l in update_lits[1:]: Up_Expr &= l
            
        transitions_data.append({
            'enable': En_Expr,
            'smooth_vars': vars_to_smooth,
            'update': Up_Expr
        })

    # --- 6. Vòng lặp tính toán Reachability (Fixed Point Iteration) ---
    print("   [BDD] Starting Fixed Point Iteration...")
    iter_count = 0
    start_loop = time.time()
    
    while True:
        iter_count += 1
        S_new_accum = None # Tập hợp các trạng thái tìm được trong bước này
        
        # Duyệt qua từng transition (Disjunctive Partitioning)
        for t_data in transitions_data:
            # 1. Tìm tập trạng thái thỏa mãn điều kiện bắn (Image Computation)
            # S_en = Reach & Enable
            S_en = Frontier & t_data['enable']
            
            if S_en.is_zero(): 
                continue
            
            # 2. Tính trạng thái tiếp theo (Next State)
            # Next = (exists involved_vars . S_en) AND Update_Logic
            if t_data['smooth_vars']:
                S_core = S_en.smoothing(t_data['smooth_vars'])
            else:
                S_core = S_en
                
            S_next = S_core & t_data['update']
            
            # Gộp vào tập trạng thái mới tìm được
            if S_new_accum is None: 
                S_new_accum = S_next
            else: 
                S_new_accum |= S_next
            
        # Điều kiện dừng: Không tìm thấy trạng thái mới nào
        if S_new_accum is None: 
            break
            
        # Chỉ giữ lại những trạng thái THỰC SỰ mới (chưa từng có trong Reach)
        New = S_new_accum & ~Reach
        
        if New.is_zero(): 
            break
            
        # Cập nhật tập Reach và Frontier
        Reach = Reach | New
        Frontier = New
        
        # print(f"      -> Iter {iter_count}: Found new states.")

    elapsed = time.time() - start_loop
    print(f"   [BDD] Finished in {elapsed:.4f}s. Counting states...")
    
    # Đếm số lượng nghiệm thỏa mãn BDD (số marking reachable)
    count = int(Reach.satisfy_count())
    return Reach, count