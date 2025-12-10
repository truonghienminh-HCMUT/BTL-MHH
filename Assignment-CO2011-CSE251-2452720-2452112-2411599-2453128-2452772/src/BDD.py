import collections
from typing import Tuple
from pyeda.inter import *
from .PetriNet import PetriNet
import numpy as np

# Build hàm reachable của BDD:
def bdd_reachable(pn: PetriNet) -> Tuple[BinaryDecisionDiagram, int]:
    
# Đọc I, O, M0 từ PetriNet
    if hasattr(pn, "I"):
        I = np.array(getattr(pn, "I"), dtype=int)
    elif hasattr(pn, "pre"):
        I = np.array(getattr(pn, "pre"), dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute I or pre")
    
    if hasattr(pn, "O"):
        O = np.array(getattr(pn, "O"), dtype=int)
    elif hasattr(pn, "post"):
        O = np.array(getattr(pn, "post"), dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute O or post")
    
    if hasattr(pn, "M0"):
        M0 = np.array(getattr(pn, "M0"), dtype=int)
    elif hasattr(pn, "initial_marking"):
        M0 = np.array(getattr(pn, "initial_marking"), dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute M0 or initial_marking")

    M0 = M0.reshape(-1)
    num_places = M0.shape[0]

    if O.shape != I.shape:
        raise ValueError("I and O must have the same shape")

    r, c = I.shape
    if c == num_places:
        row_is_transition = True   # I[t, p]
        num_trans = r
    elif r == num_places:
        row_is_transition = False  # I[p, t]
        num_trans = c
    else:
        raise ValueError("Shape of I does not match number of places/transitions")

    def pre_vec(index_t: int) -> np.ndarray:
        return I[index_t, :] if row_is_transition else I[:, index_t]
    
    def post_vec(index_t: int) -> np.ndarray:
        return O[index_t, :] if row_is_transition else O[:, index_t]

# Lấy danh sách tên place
    places = None

    if hasattr(pn, "P"):
        val = getattr(pn, "P")
        places = list(val)
    elif hasattr(pn, "places"):
        raw_places = list(getattr(pn, "places"))
        if raw_places and hasattr(raw_places[0], "name"):
            places = [p.name for p in raw_places]
        else:
            places = [str(p) for p in raw_places]

    if places is None:
        for attr, val in vars(pn).items():
            if isinstance(val, (list, tuple)) and len(val) == num_places and len(val) > 0:
                first = val[0]
                if isinstance(first, str) or hasattr(first, "name"):
                    if hasattr(first, "name"):
                        places = [x.name for x in val]
                    else:
                        places = list(val)
                    break

    if places is None:
        places = [f"p{i+1}" for i in range(num_places)]

# SYMBOLIC: tạo BDD variables
# Biến cho marking hiện tại x_p và marking kế tiếp x'_p
# BDDVariable cho x:
    cur_vars = [bddvar(str(name)) for name in places]       
# BDDVariable cho x':    
    next_vars = [bddvar(f"{name}_next") for name in places]     

# BDD Initial: encode M0
    init_lits = []
    for bit, x in zip(M0, cur_vars):
        init_lits.append(x if int(bit) else ~x)

# M0 chắc chắn có ít nhất 1 place nên And(*init_lits) sẽ thoả mãn
    Reach = init_lits[0]
    for lit in init_lits[1:]:
        Reach = Reach & lit
    Frontier = Reach

# Build TR:
    TR = None 

    for t in range(num_trans):
        pre_t = pre_vec(t)
        post_t = post_vec(t)

        lits = []
        for p in range(num_places):
            pre = 1 if int(pre_t[p]) > 0 else 0
            post = 1 if int(post_t[p]) > 0 else 0

            x = cur_vars[p]
            xp = next_vars[p]

            if pre == 1 and post == 0:
# Sử dụngtoken: 1 -> 0:
                lits.append(x & ~xp)
            elif pre == 0 and post == 1:
# Tạo token: 0 -> 1:
                lits.append(~x & xp)
            elif pre == 1 and post == 1:
# self-loop: 1 -> 1:
                lits.append(x & xp)
            else: 
# Giữ nguyên: xp == x:
                lits.append((x & xp) | (~x & ~xp))

# R_t(x,x') bằng với tổng hợp các tất cả literal:
        Rt = lits[0]
        for lit in lits[1:]:
            Rt = Rt & lit

        if TR is None:
            TR = Rt
        else:
            TR = TR | Rt

    if TR is None:
        bdd = Reach
        count = int(bdd.satisfy_count())
        return bdd, count

# Dùng BDDVariable
    cur_vars_seq = tuple(cur_vars)
    rename_map = {xp: x for xp, x in zip(next_vars, cur_vars)}

# Lặp symbolic image
    while True:
        step = Frontier & TR
        post = step.smoothing(cur_vars_seq)
        
# Chỉnh x'_p -> x_p để đưa về không gian biến hiện tại
        post_cur = post.compose(rename_map)
        
# New(x) = Post_cur(x) \ Reach(x)
        New = post_cur & ~Reach
        if New.is_zero():
            break
        Reach = Reach | New
        Frontier = New
    bdd = Reach
    count = int(bdd.satisfy_count())
    return bdd, count

