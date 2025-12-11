import numpy as np
from typing import List, Optional
import pulp
import random
from pyeda.inter import BinaryDecisionDiagram
from src.PetriNet import PetriNet

def deadlock_reachable_marking(
    pn: PetriNet,
    reachable_bdd: "BinaryDecisionDiagram",
) -> Optional[List[int]]:
    """
    Tìm một deadlock marking sử dụng phương pháp lai giữa ILP và BDD (Task 4).
    Đã tối ưu hóa bằng cách Randomize hàm mục tiêu để thoát khỏi các vùng deadlock giả.
    """
    print("  > Initializing ILP for Deadlock Detection...")

    # --- 1. Lấy ma trận Incidence và thông tin Petri Net -------------------
    if hasattr(pn, "I"):
        I = np.array(pn.I, dtype=int)
    elif hasattr(pn, "pre"):
        I = np.array(pn.pre, dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute I or pre")

    if hasattr(pn, "O"):
        O = np.array(pn.O, dtype=int)
    elif hasattr(pn, "post"):
        O = np.array(pn.post, dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute O or post")

    # Lấy danh sách tên Place chuẩn
    if hasattr(pn, "place_ids"):
        place_names = list(pn.place_ids)
    else:
        # Fallback nếu không có place_ids
        num_places_temp = I.shape[1] if I.shape[0] != len(getattr(pn, 'transitions', [])) else I.shape[0]
        place_names = [f"p{i+1}" for i in range(num_places_temp)]
    
    num_places = len(place_names)
    
    # --- XỬ LÝ ORIENTATION (QUAN TRỌNG) ---
    r, c = I.shape
    row_is_place = False 
    if hasattr(pn, "transitions"):
        if len(pn.transitions) == c and len(pn.transitions) != r:
            row_is_place = True
    if row_is_place is False and r == num_places and c != num_places:
        row_is_place = True

    num_trans = c if row_is_place else r

    def get_input_places(t_idx):
        return np.where(I[:, t_idx] > 0)[0] if row_is_place else np.where(I[t_idx, :] > 0)[0]

    def get_output_places(t_idx):
        return np.where(O[:, t_idx] > 0)[0] if row_is_place else np.where(O[t_idx, :] > 0)[0]

    # --- 2. Khởi tạo bài toán ILP ------------------------------------------
    prob = pulp.LpProblem("Deadlock_Detection", pulp.LpMinimize)
    m_vars = [pulp.LpVariable(f"m_{i}", cat='Binary') for i in range(num_places)]

    # --- 3. Thêm ràng buộc Structural Deadlock -------------------
    # Transition disabled <==> (Inputs Missing) OR (Safety Violation)
    big_M = num_places + 5
    
    for t in range(num_trans):
        inputs = get_input_places(t)
        outputs = get_output_places(t)
        pure_outputs = [idx for idx in outputs if idx not in inputs]
        n_inputs = len(inputs)
        
        delta = pulp.LpVariable(f"delta_t{t}", cat='Binary')
        
        # Condition 1: Missing tokens input
        if n_inputs > 0:
            prob += pulp.lpSum([m_vars[i] for i in inputs]) <= (n_inputs - 1) + big_M * delta
        else:
            prob += 0 <= -1 + big_M * delta # Source transition -> always enabled unless delta=1

        # Condition 2: Output place full (1-safe property)
        if len(pure_outputs) > 0:
             prob += pulp.lpSum([m_vars[i] for i in pure_outputs]) >= 1 - big_M * (1 - delta)
        else:
            prob += 0 >= 1 - big_M * (1 - delta)

    # --- 4. Hàm kiểm tra BDD (Robust Mapping) ---------------------------
    # Tạo map từ tên biến trong BDD sang index của m_vars
    # BDD variables có thể là "P1", "p1", "place_1"... tùy vào lúc tạo
    place_map = {name: i for i, name in enumerate(place_names)}

    def check_reachability_bdd(marking_list):
        if reachable_bdd is None: return True
        
        point = {}
        # Duyệt qua các biến thực sự có trong BDD
        for var in reachable_bdd.support:
            vname = str(var)
            idx = place_map.get(vname)
            
            # Thử các case khác nhau để map
            if idx is None: idx = place_map.get(vname.lower())
            if idx is None: idx = place_map.get(vname.upper())
            
            if idx is not None and idx < len(marking_list):
                point[var] = int(marking_list[idx])
        
        # Nếu point rỗng (do map sai hoặc BDD là hằng số), xử lý riêng
        if not point:
            return not reachable_bdd.is_zero()
            
        # Restrict BDD tại điểm marking
        result_bdd = reachable_bdd.restrict(point)
        return result_bdd.is_one()

    # --- 5. Vòng lặp giải ILP (HEURISTIC OPTIMIZATION) ----------------------
    # Sử dụng solver mặc định nhưng tắt log để đỡ rối
    solver = pulp.PULP_CBC_CMD(msg=False) 
    
    attempt = 0
    max_attempts = 100 # Giới hạn số lần thử để tránh treo máy quá lâu
    
    print(f"  > Starting Iterative Search (Max {max_attempts} attempts)...")

    while attempt < max_attempts:
        attempt += 1
        
        # [OPTIMIZATION] Randomize hàm mục tiêu!
        # Điều này giúp Solver không bị kẹt ở một vùng nghiệm cục bộ (local minima)
        # Lúc thì tìm marking ít token, lúc thì tìm nhiều token, lúc thì ngẫu nhiên.
        mode = attempt % 3
        if mode == 0:
            # Ưu tiên tìm marking có ít token nhất (thường deadlock là trạng thái cạn kiệt)
            prob.setObjective(pulp.lpSum(m_vars)) 
        elif mode == 1:
            # Ưu tiên tìm marking nhiều token (bị kẹt do safety)
            prob.setObjective(-pulp.lpSum(m_vars))
        else:
            # Random hoàn toàn để nhảy cóc
            weights = [random.randint(-2, 2) for _ in range(num_places)]
            prob.setObjective(pulp.lpSum([w * v for w, v in zip(weights, m_vars)]))

        prob.solve(solver)

        if prob.status != pulp.LpStatusOptimal:
            print("  > ILP Infeasible. No structural deadlock exists.")
            return None

        try:
            current_marking = [int(round(var.varValue)) for var in m_vars]
        except:
            return None
        
        # Check BDD
        if check_reachability_bdd(current_marking):
            print(f"  > FOUND Reachable Deadlock at attempt {attempt}!")
            return current_marking
        else:
            # Nếu không reachable, thêm Canonical Cut để loại bỏ nghiệm này
            if attempt % 10 == 0:
                print(f"    - Attempt {attempt}: Found spurious dead marking (unreachable). Cutting and retrying...")
                
            ones = [i for i, val in enumerate(current_marking) if val == 1]
            zeros = [i for i, val in enumerate(current_marking) if val == 0]
            
            # Constraint: Sum(Ones) - Sum(Zeros) <= |Ones| - 1
            # Ràng buộc này chỉ loại bỏ DUY NHẤT marking hiện tại
            prob += (
                pulp.lpSum([m_vars[i] for i in ones]) - 
                pulp.lpSum([m_vars[j] for j in zeros]) 
                <= len(ones) - 1
            ), f"Cut_{attempt}"
    
    print("  > Max attempts reached. Could not find reachable deadlock.")
    return None