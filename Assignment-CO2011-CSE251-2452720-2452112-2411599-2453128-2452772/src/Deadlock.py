import numpy as np
from typing import List, Optional
import pulp
from pyeda.inter import BinaryDecisionDiagram
from src.PetriNet import PetriNet

def deadlock_reachable_marking(
    pn: PetriNet,
    reachable_bdd: "BinaryDecisionDiagram",
) -> Optional[List[int]]:
    """
    Tìm một deadlock marking sử dụng phương pháp lai giữa ILP và BDD (Task 4).
    
    Cập nhật logic cho mạng 1-safe:
    Transition t bị disable nếu:
    1. (Resource Deadlock) Thiếu token ở input places.
       HOẶC
    2. (Safety Deadlock) Place output (pure output) đã có token (gây violation 1-safe).
    """

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

    # Lấy danh sách tên Place
    if hasattr(pn, "place_ids"):
        place_names = list(pn.place_ids)
    else:
        num_places_temp = I.shape[1] 
        place_names = [f"p{i+1}" for i in range(num_places_temp)]
    
    num_places = len(place_names)
    
    # --- XỬ LÝ ORIENTATION (QUAN TRỌNG CHO TEST CASE) ---
    r, c = I.shape
    
    # Mặc định ưu tiên Row=Transition (phổ biến trong test manual như test_002)
    # Trừ khi số hàng khớp số places và số cột khác số places
    row_is_place = False 
    
    if hasattr(pn, "transitions"):
        # Nếu có thông tin chính xác về số lượng transitions, dùng để định hướng
        if len(pn.transitions) == c and len(pn.transitions) != r:
            row_is_place = True
        elif len(pn.transitions) == r:
            row_is_place = False
    
    # Fallback dựa trên shape nếu không có info
    if row_is_place is False and r == num_places and c != num_places:
        row_is_place = True

    num_trans = c if row_is_place else r

    # Helpers lấy input/output indices
    def get_input_places(t_idx):
        if row_is_place:
            return np.where(I[:, t_idx] > 0)[0]
        else:
            return np.where(I[t_idx, :] > 0)[0]

    def get_output_places(t_idx):
        if row_is_place:
            return np.where(O[:, t_idx] > 0)[0]
        else:
            return np.where(O[t_idx, :] > 0)[0]

    # --- 2. Khởi tạo bài toán ILP ------------------------------------------
    prob = pulp.LpProblem("Deadlock_Detection", pulp.LpMinimize)

    # Biến nhị phân cho Marking (0 hoặc 1 do 1-safe)
    m_vars = [pulp.LpVariable(f"m_{i}", cat='Binary') for i in range(num_places)]

    # Hàm mục tiêu giả
    prob += 0, "Arbitrary_Objective"

    # --- 3. Thêm ràng buộc Structural Deadlock (Updated) -------------------
    # Transition t DISABLED <==> (Inputs Missing) OR (Pure Outputs Full)
    # Sử dụng kỹ thuật Big-M với biến nhị phân delta_t
    # delta_t = 0 => Force Input Constraint
    # delta_t = 1 => Force Output Constraint
    
    big_M = num_places + 1  # Đủ lớn
    
    for t in range(num_trans):
        inputs = get_input_places(t)
        outputs = get_output_places(t)
        
        # Pure outputs: output places that are not input places (ignore self-loops)
        pure_outputs = [idx for idx in outputs if idx not in inputs]
        
        n_inputs = len(inputs)
        
        # Biến điều khiển switch cho điều kiện OR
        delta = pulp.LpVariable(f"delta_t{t}", cat='Binary')
        
        # Constraint A: Missing Inputs
        # Sum(inputs) <= n_inputs - 1
        # Relaxed: Sum(inputs) <= (n_inputs - 1) + M * delta
        if n_inputs > 0:
            prob += pulp.lpSum([m_vars[i] for i in inputs]) <= (n_inputs - 1) + big_M * delta, f"Dis_In_t{t}"
        else:
            # Nếu không có input (Source), điều kiện này luôn False (0 <= -1), 
            # buộc delta phải = 1 (chuyển sang check output)
            prob += 0 <= -1 + big_M * delta, f"Dis_In_Source_t{t}"

        # Constraint B: Output Full (Safety violation)
        # Sum(pure_outputs) >= 1 (Có ít nhất 1 chỗ output đã bị chiếm)
        # Relaxed: Sum(pure_outputs) >= 1 - M * (1 - delta)
        if len(pure_outputs) > 0:
             prob += pulp.lpSum([m_vars[i] for i in pure_outputs]) >= 1 - big_M * (1 - delta), f"Dis_Out_t{t}"
        else:
            # Nếu không có pure output (Sink hoặc Loop), điều kiện này luôn False (0 >= 1),
            # buộc delta phải = 0 (chuyển sang check input)
            prob += 0 >= 1 - big_M * (1 - delta), f"Dis_Out_Sink_t{t}"

    # --- 4. Hàm kiểm tra tính Reachable bằng BDD ---------------------------
    place_map = {name: i for i, name in enumerate(place_names)}

    def check_reachability_bdd(marking_list):
        if reachable_bdd is None:
            return True
        
        point = {}
        for var in reachable_bdd.support:
            vname = str(var)
            idx = place_map.get(vname)
            
            # Fallback case-insensitive
            if idx is None:
                for name, i in place_map.items():
                    if name.lower() == vname.lower():
                        idx = i
                        break
            
            if idx is not None and idx < len(marking_list):
                point[var] = int(marking_list[idx])
        
        if not point:
            return reachable_bdd.is_one()
            
        return reachable_bdd.restrict(point).is_one()

    # --- 5. Vòng lặp giải ILP & Kiểm tra BDD -------------------------------
    solver = pulp.PULP_CBC_CMD(msg=False) 
    attempt = 0
    max_attempts = 1000

    while attempt < max_attempts:
        attempt += 1
        prob.solve(solver)

        if prob.status != pulp.LpStatusOptimal:
            return None

        try:
            current_marking = [int(round(var.varValue)) for var in m_vars]
        except (TypeError, ValueError):
            return None
        
        # Debug print nếu cần thiết
        # print(f"ILP found dead marking: {current_marking}")

        if check_reachability_bdd(current_marking):
            return current_marking
        else:
            # Spurious Deadlock -> Add canonical cut
            ones = [i for i, val in enumerate(current_marking) if val == 1]
            zeros = [i for i, val in enumerate(current_marking) if val == 0]
            
            prob += (
                pulp.lpSum([m_vars[i] for i in ones]) - 
                pulp.lpSum([m_vars[j] for j in zeros]) 
                <= len(ones) - 1
            ), f"Cut_{attempt}"
    
    return None