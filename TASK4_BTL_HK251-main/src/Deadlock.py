import numpy as np
from typing import List, Optional
import pulp
from pyeda.inter import BinaryDecisionDiagram
from src.PetriNet import PetriNet
import scipy.linalg # Cần thêm thư viện này để tính Null Space

def get_p_invariants(I, O):
    """
    Tính P-invariants dựa trên Incidence Matrix C = O - I.
    Tìm y sao cho y.T * C = 0.
    """
    try:
        C = O - I
        # Sử dụng scipy để tìm null space (ker) của C chuyển vị
        # Null space của C^T chính là P-invariants
        null_space = scipy.linalg.null_space(C.T)
        
        # Làm tròn số để loại bỏ sai số dấu phẩy động và chuyển về số nguyên
        invariants = []
        for i in range(null_space.shape[1]):
            vec = null_space[:, i]
            # Chuẩn hóa vector để dễ nhìn (chia cho số nhỏ nhất khác 0)
            min_val = np.min(np.abs(vec[np.abs(vec) > 1e-5]))
            vec = vec / min_val
            vec = np.round(vec).astype(int)
            invariants.append(vec)
        return invariants
    except Exception as e:
        print(f"[WARN] Không thể tự động tính P-Invariants: {e}")
        return []

def deadlock_reachable_marking(
    pn: PetriNet,
    reachable_bdd: "BinaryDecisionDiagram",
) -> Optional[List[int]]:
    
    # --- 1. Lấy ma trận Incidence -------------------
    # (Giữ nguyên phần xử lý lấy I, O, place_names từ code cũ của bạn)
    if hasattr(pn, "I"):
        I = np.array(pn.I, dtype=int)
    elif hasattr(pn, "pre"):
        I = np.array(pn.pre, dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute I/pre")

    if hasattr(pn, "O"):
        O = np.array(pn.O, dtype=int)
    elif hasattr(pn, "post"):
        O = np.array(pn.post, dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute O/post")

    if hasattr(pn, "place_ids"):
        place_names = list(pn.place_ids)
    else:
        num_places_temp = I.shape[1] 
        place_names = [f"p{i+1}" for i in range(num_places_temp)]
    
    num_places = len(place_names)
    
    # --- XỬ LÝ ORIENTATION (Giữ nguyên) ---
    r, c = I.shape
    row_is_place = False 
    if hasattr(pn, "transitions"):
        if len(pn.transitions) == c and len(pn.transitions) != r:
            row_is_place = True
        elif len(pn.transitions) == r:
            row_is_place = False
    if row_is_place is False and r == num_places and c != num_places:
        row_is_place = True

    # Chuẩn hóa I, O về dạng (Place x Transition) để tính toán toán học
    if not row_is_place:
        I_mat = I.T
        O_mat = O.T
    else:
        I_mat = I
        O_mat = O
        
    num_trans = I_mat.shape[1]

    # --- 2. Khởi tạo ILP ------------------------------------------
    prob = pulp.LpProblem("Deadlock_Detection", pulp.LpMinimize)
    m_vars = [pulp.LpVariable(f"m_{i}", cat='Binary') for i in range(num_places)]
    prob += 0, "Arbitrary_Objective"

    # --- [MỚI] 3. Thêm Ràng buộc P-Invariants (Chìa khóa tăng tốc) ---
    # Mục tiêu: m_hientai * y = m0 * y
    # Điều này loại bỏ các trạng thái "phi vật lý" (Process biến mất, Resource nhân đôi...)
    
    # Lấy Initial Marking
    if hasattr(pn, "initial_marking"):
        m0 = np.array(pn.initial_marking, dtype=int)
    elif hasattr(pn, "m0"):
        m0 = np.array(pn.m0, dtype=int)
    else:
        m0 = np.zeros(num_places, dtype=int) # Fallback

    invariants = get_p_invariants(I_mat, O_mat)
    
    print(f"   [ILP] Found {len(invariants)} P-Invariants. Adding constraints...")
    for idx, inv in enumerate(invariants):
        # Initial token count for this invariant
        token_sum_initial = np.dot(inv, m0)
        
        # Constraint: Sum(weight * m_i) == Initial_Sum
        prob += pulp.lpSum([inv[i] * m_vars[i] for i in range(num_places)]) == token_sum_initial, f"Invariant_{idx}"

    # --- 4. Ràng buộc Structural Deadlock (Giữ nguyên logic cũ) ---
    big_M = num_places + 5
    
    for t in range(num_trans):
        # Lấy input/output dựa trên matrix đã chuẩn hóa (Rows = Places)
        inputs = np.where(I_mat[:, t] > 0)[0]
        outputs = np.where(O_mat[:, t] > 0)[0]
        pure_outputs = [x for x in outputs if x not in inputs]
        
        delta = pulp.LpVariable(f"delta_t{t}", cat='Binary')
        
        # Missing Input constraint
        if len(inputs) > 0:
            prob += pulp.lpSum([m_vars[i] for i in inputs]) <= (len(inputs) - 1) + big_M * delta
        else:
            prob += 0 <= -1 + big_M * delta # Always false -> delta=1

        # Output Full constraint
        if len(pure_outputs) > 0:
             prob += pulp.lpSum([m_vars[i] for i in pure_outputs]) >= 1 - big_M * (1 - delta)
        else:
            prob += 0 >= 1 - big_M * (1 - delta) # Always false -> delta=0

    # --- 5. Hàm check BDD & Loop (Giữ nguyên) -----------------------
    place_map = {name: i for i, name in enumerate(place_names)}

    def check_reachability_bdd(marking_list):
        if reachable_bdd is None: return True
        point = {}
        for var in reachable_bdd.support:
            vname = str(var)
            idx = place_map.get(vname)
            # Fallback map logic...
            if idx is None:
                for name, i in place_map.items():
                    if name.lower() == vname.lower():
                        idx = i; break
            if idx is not None and idx < len(marking_list):
                point[var] = int(marking_list[idx])
        if not point: return reachable_bdd.is_one()
        return reachable_bdd.restrict(point).is_one()

    solver = pulp.PULP_CBC_CMD(msg=False) 
    attempt = 0
    max_attempts = 100 # Giảm xuống vì Invariant đã lọc rất tốt
    
    print("   [ILP] Starting Iterative Search...")

    while attempt < max_attempts:
        attempt += 1
        prob.solve(solver)

        if prob.status != pulp.LpStatusOptimal:
            return None

        current_marking = [int(round(var.varValue)) for var in m_vars]
        
        if check_reachability_bdd(current_marking):
            return current_marking # Tìm thấy Deadlock thật!
        else:
            # Canonical Cut: Loại bỏ trạng thái giả này
            ones = [i for i, val in enumerate(current_marking) if val == 1]
            zeros = [i for i, val in enumerate(current_marking) if val == 0]
            prob += (pulp.lpSum([m_vars[i] for i in ones]) - pulp.lpSum([m_vars[j] for j in zeros]) <= len(ones) - 1)
    
    return None