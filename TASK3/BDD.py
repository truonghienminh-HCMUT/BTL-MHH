import collections
from typing import Tuple
from pyeda.inter import *
from PetriNet import PetriNet
from collections import deque
import numpy as np


# Lấy ma trận I (input), O (output) và marking ban đầu M0:
def bdd_reachable(pn: PetriNet) -> Tuple[BinaryDecisionDiagram, int]:
    
# I: số token cần ở mỗi place để firing transition:
    if hasattr(pn, "I"):
        I = np.array(getattr(pn, "I"), dtype=int)
    elif hasattr(pn, "pre"):
        I = np.array(getattr(pn, "pre"), dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute I or pre")
    
# O: số token được thêm vào mỗi place sau khi firing transition
    if hasattr(pn, "O"):
        O = np.array(getattr(pn, "O"), dtype=int)
    elif hasattr(pn, "post"):
        O = np.array(getattr(pn, "post"), dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute O or post")
    
# M0: marking ban đầu
    if hasattr(pn, "M0"):
        M0 = np.array(getattr(pn, "M0"), dtype=int)
    elif hasattr(pn, "initial_marking"):
        M0 = np.array(getattr(pn, "initial_marking"), dtype=int)
    else:
        raise AttributeError("PetriNet object must have attribute M0 or initial_marking")

# Đưa M0 về vector 1 chiều, độ dài = số place
    M0 = M0.reshape(-1)
    num_places = M0.shape[0]

# Xác định số transition và orientation của I, O:
# Rào shape của I và O nếu khác nhau:
    if O.shape != I.shape:
        raise ValueError("I and O must have the same shape")

    r, c = I.shape  
    
# I có dạng (num_trans, num_places) -> mỗi hàng là 1 transition:
    if c == num_places:
        row_is_transition = True   # I[t, p]
        num_trans = r
        
# I có dạng (num_places, num_trans) -> mỗi cột là 1 transition:
    elif r == num_places:
        row_is_transition = False  # I[p, t]
        num_trans = c
        
# Nếu không thoả cả 3 TH trên:
    else:
        raise ValueError("Shape of I does not match number of places/transitions")


# Lấy vector pre của transition index index_t:
    def pre_vec(index_t: int) -> np.ndarray:
        # vector độ dài = num_places: pre yêu cầu ở mỗi place
        return I[index_t, :] if row_is_transition else I[:, index_t]
    
# Lấy vector post của transition index_t:
    def post_vec(index_t: int) -> np.ndarray:
        # vector độ dài = num_places: post cộng thêm ở mỗi place
        return O[index_t, :] if row_is_transition else O[:, index_t]

# Lấy danh sách cho Place:
    places = None

# Đặt "P" là tập các Place, xét nếu pn thuộc "P" thì kéo về list của "places"
    if hasattr(pn, "P"):
        val = getattr(pn, "P")
        places = list(val)

# Nếu không có trong "P", thì nhảy qua tìm trong "places"
    elif hasattr(pn, "places"):
        raw_places = list(getattr(pn, "places"))
        
# Nếu phần tử có đuôi .name thì lấy theo tên:
        if raw_places and hasattr(raw_places[0], "name"):
            places = [p.name for p in raw_places]
            
# Còn không, sẽ lấy theo kiểu string
        else:
            places = [str(p) for p in raw_places]

# Và nếu Place vẫn chưa tìm được, quét các field khác trong pn để đoán
    if places is None:
        for attr, val in vars(pn).items():
            
# Tìm list và các tuple có đúng số phần tử = num_places và phần tử có thể là tên
            if isinstance(val, (list, tuple)) and len(val) == num_places and len(val) > 0:
                first = val[0]
                if isinstance(first, str) or hasattr(first, "name"):
                    if hasattr(first, "name"):
                        places = [x.name for x in val]
                    else:
                        places = list(val)
                    break

# Nếu không có tên, sẽ tạo tên theo kiểu thứ tự p1, p2, ...
    if places is None:
        places = [f"p{i+1}" for i in range(num_places)]

# BFS explicit trên không gian marking (state space)
# Node: marking M (vector 0/1)    
# Cạnh: M --t--> M' nếu t enabled tại M và firing t thu được M'

    start = tuple(int(x) for x in M0)  # marking ban đầu
    visited = {start}                  # tập các marking đã thăm
    q = deque([start])                 # hàng đợi BFS

    while q:
        mark = q.popleft()
        M = np.array(mark, dtype=int)

        for t in range(num_trans):
            pre_t = pre_vec(t)
            post_t = post_vec(t)

# t enabled khi đủ token ở tất cả input places
            if np.all(M >= pre_t):
                
# firing t: M_next = M - pre + post
                M_next = M - pre_t + post_t

# Net 1-safe: nếu có place nào > 1 token thì bỏ qua trạng thái này
                if np.any(M_next > 1):
                    continue

# Chuyển sang tuple để dùng trong set visited
                next_tuple = tuple(int(x) for x in M_next)
                if next_tuple not in visited:
                    visited.add(next_tuple)
                    q.append(next_tuple)

# Biểu diễn tập reachable marking
# Mỗi place -> 1 biến Boolean x_i
# Mỗi marking M -> 1 cube
# BDD = biểu thức hoặc của tất cả các cube
# Tạo biến Boolean tương ứng với mỗi place
    vars_by_place = [exprvar(str(name)) for name in places]
    cubes = []
    for mark in visited:
        
# mark là tuple gồm 0/1 tương ứng với token ở mỗi place
        lits = []
        for bit, var in zip(mark, vars_by_place):
# bit = 1  -> literal là var
# bit = 0  -> literal là ~var
            lits.append(var if bit else ~var)
        cubes.append(And(*lits))   # cube là tổng hợp tất cả literal

# Về False nếu không có reachable marking nào:
    bool_expr = expr(False) if not cubes else Or(*cubes)

# Chuyển Expr thành BDD, và count = số marking reachable
    bdd = expr2bdd(bool_expr)
    count = len(visited)
    return bdd, count
