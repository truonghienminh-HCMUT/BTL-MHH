import numpy as np
from typing import List, Tuple, Optional

from PetriNet import PetriNet
from .BDD import bdd_reachable
from pyeda.inter import bdd2expr, exprvar, BinaryDecisionDiagram
from collections import deque
import pulp


def deadlock_reachable_marking(
    pn: PetriNet,
    reachable_bdd: "BinaryDecisionDiagram",
) -> Optional[List[int]]:
    """
    Tìm một marking vừa:
      - reachable từ M0 của Petri Net pn (với điều kiện 1-safe)
      - thỏa BDD 'reachable_bdd'
      - và là deadlock (không còn transition nào enabled)

    Nếu không có marking nào như vậy -> trả về None.
    """

    # --- 1. Lấy I, O, M0 từ PetriNet ---------------------------------------
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

    if hasattr(pn, "M0"):
        M0 = np.array(pn.M0, dtype=int)
    elif hasattr(pn, "initial_marking"):
        M0 = np.array(pn.initial_marking, dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute M0 or initial_marking")

    # Đưa về vector 1 chiều
    M0 = M0.reshape(-1)
    num_places = M0.shape[0]

    # --- 2. Xác định orientation của I, O -----------------------------------
    if I.shape != O.shape:
        raise ValueError("I and O must have the same shape")

    r, c = I.shape
    if c == num_places:
        # I[t, p] – mỗi hàng là 1 transition
        row_is_transition = True
        num_trans = r
    elif r == num_places:
        # I[p, t] – mỗi cột là 1 transition
        row_is_transition = False
        num_trans = c
    else:
        raise ValueError("Shape of I does not match number of places/transitions")

    def pre_vec(t_idx: int) -> np.ndarray:
        return I[t_idx, :] if row_is_transition else I[:, t_idx]

    def post_vec(t_idx: int) -> np.ndarray:
        return O[t_idx, :] if row_is_transition else O[:, t_idx]

    # --- 3. Lấy tên place để map sang biến trong BDD -----------------------
    if hasattr(pn, "place_ids"):
        places = list(pn.place_ids)
    else:
        # fallback đơn giản – đánh số p0, p1, ...
        places = [f"p{i+1}" for i in range(num_places)]

    place_index = {name: idx for idx, name in enumerate(places)}

    # Hàm: marking có thỏa BDD reachable_bdd hay không
    def marking_satisfies_bdd(marking: np.ndarray) -> bool:
        if reachable_bdd is None:
            # Nếu không đưa BDD vào thì coi như mọi marking đều hợp lệ
            return True

        # Tạo "point" cho các biến có trong BDD (support)
        point = {}
        for var in reachable_bdd.support:
            vname = str(var)  # ví dụ 'p1', 'p2', ...
            idx = place_index.get(vname, None)
            if idx is None:
                # Biến không thuộc danh sách place -> bỏ qua
                continue
            point[var] = int(marking[idx])

        # Nếu BDD không phụ thuộc vào biến nào -> nó là hằng 0 hoặc 1
        if not point:
            return reachable_bdd.is_one()

        # restricted là BDD sau khi gán các biến theo marking
        restricted = reachable_bdd.restrict(point)
        return restricted.is_one()

    # --- 4. Kiểm tra transition enabled với điều kiện 1-safe ---------------
    def is_enabled(marking: np.ndarray, t_idx: int) -> bool:
        pre = pre_vec(t_idx)
        post = post_vec(t_idx)

        # Điều kiện 1: đủ token ở các place input
        if np.any(marking < pre):
            return False

        # Điều kiện 2: sau khi fire vẫn không vượt quá 1 token / place
        new_marking = marking - pre + post
        if np.any(new_marking > 1):
            return False

        return True

    def fire(marking: np.ndarray, t_idx: int) -> np.ndarray:
        pre = pre_vec(t_idx)
        post = post_vec(t_idx)
        return marking - pre + post

    # --- 5. BFS trên không gian reachable markings -------------------------
    visited = set()
    q = deque()

    init_tuple = tuple(int(x) for x in M0.tolist())
    visited.add(init_tuple)
    q.append(M0)

    while q:
        M = q.popleft()

        # 5.1. Nếu marking nằm trong BDD và là deadlock -> trả về
        if marking_satisfies_bdd(M):
            any_enabled = False
            for t_idx in range(num_trans):
                if is_enabled(M, t_idx):
                    any_enabled = True
                    break

            if not any_enabled:
                # Deadlock reachable & thỏa BDD
                return [int(x) for x in M.tolist()]

        # 5.2. Sinh các marking kế tiếp bằng cách fire từng transition enabled
        for t_idx in range(num_trans):
            if is_enabled(M, t_idx):
                M_next = fire(M, t_idx)
                key = tuple(int(x) for x in M_next.tolist())
                if key not in visited:
                    visited.add(key)
                    q.append(M_next)

    # Không có deadlock nào thỏa BDD
    return None
