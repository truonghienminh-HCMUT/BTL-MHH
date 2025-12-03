from typing import List, Optional
from collections import deque

import numpy as np
import pulp
from pyeda.inter import BinaryDecisionDiagram, bdd2expr, exprvar

from .PetriNet import PetriNet


def deadlock_reachable_marking(
    pn: PetriNet,
    reachable_bdd: Optional[BinaryDecisionDiagram],
    method: str = "ilp",
) -> Optional[List[int]]:
    """Tìm deadlock reachable thỏa BDD bằng ILP (mặc định) hoặc BFS fallback."""

    if method not in {"ilp", "bfs"}:
        raise ValueError("method must be either 'ilp' or 'bfs'")

    if method == "bfs" or reachable_bdd is None:
        return _deadlock_reachable_marking_bfs(pn, reachable_bdd)

    result = _deadlock_reachable_marking_ilp(pn, reachable_bdd)
    if result is not None or method == "ilp":
        return result

    # Nếu ILP không tìm được (hoặc solver trả về infeasible) thì fallback BFS
    return _deadlock_reachable_marking_bfs(pn, reachable_bdd)


def _get_places_from_petrinet(pn: PetriNet) -> List[str]:
    """Trích danh sách place để map với biến của BDD/ILP."""

    if hasattr(pn, "place_ids"):
        return list(pn.place_ids)
    if hasattr(pn, "P"):
        return list(getattr(pn, "P"))
    if hasattr(pn, "places"):
        places = list(getattr(pn, "places"))
        if places and hasattr(places[0], "name"):
            return [p.name for p in places]
        return [str(p) for p in places]

    m0 = getattr(pn, "M0", None) or getattr(pn, "initial_marking", None)
    if m0 is not None:
        num_places = int(np.array(m0, dtype=int).reshape(-1).shape[0])
        # Thử quét các attribute dạng list/tuple để tìm tên
        for attr, val in vars(pn).items():
            if isinstance(val, (list, tuple)) and len(val) == num_places and val:
                first = val[0]
                if isinstance(first, str):
                    return list(val)
                if hasattr(first, "name"):
                    return [obj.name for obj in val]
        return [f"p{i+1}" for i in range(num_places)]

    raise ValueError("Cannot infer places from PetriNet")


def _get_pre_matrix(pn: PetriNet):
    if hasattr(pn, "I"):
        I = np.array(getattr(pn, "I"), dtype=int)
    elif hasattr(pn, "pre"):
        I = np.array(getattr(pn, "pre"), dtype=int)
    else:
        raise AttributeError("PetriNet must have attribute I or pre")

    if hasattr(pn, "M0"):
        M0 = np.array(getattr(pn, "M0"), dtype=int).reshape(-1)
    elif hasattr(pn, "initial_marking"):
        M0 = np.array(getattr(pn, "initial_marking"), dtype=int).reshape(-1)
    else:
        raise AttributeError("PetriNet must have attribute M0 or initial_marking")

    num_places = M0.shape[0]
    r, c = I.shape

    if c == num_places:
        row_is_transition = True
        num_trans = r
    elif r == num_places:
        row_is_transition = False
        num_trans = c
    else:
        raise ValueError("Shape of pre matrix does not match number of places")

    return I, row_is_transition, num_trans, num_places


def _pre_vec(I: np.ndarray, row_is_transition: bool, index_t: int) -> np.ndarray:
    return I[index_t, :] if row_is_transition else I[:, index_t]


def _build_deadlock_ilp_model(pn: PetriNet):
    I, row_is_transition, num_trans, num_places = _get_pre_matrix(pn)

    prob = pulp.LpProblem("DeadlockSearch", pulp.LpMinimize)
    x_vars = [
        pulp.LpVariable(f"x_{i}", lowBound=0, upBound=1, cat="Binary")
        for i in range(num_places)
    ]
    prob += 0, "DummyObjective"

    for t in range(num_trans):
        pre_t = _pre_vec(I, row_is_transition, t)
        pre_indices = [i for i, val in enumerate(pre_t) if val > 0]

        if not pre_indices:
            # Transition không có input -> luôn enabled => mạng không thể deadlock
            prob += 0 <= -1, f"no_deadlock_due_to_source_transition_{t}"
            continue

        lhs = pulp.lpSum(x_vars[i] for i in pre_indices)
        prob += lhs <= len(pre_indices) - 1, f"t{t}_not_enabled"

    places = _get_places_from_petrinet(pn)
    return prob, x_vars, places


def _forbid_marking(prob: pulp.LpProblem, x_vars, marking: np.ndarray) -> None:
    n = len(marking)
    expr = pulp.lpSum(x if bit == 1 else (1 - x) for x, bit in zip(x_vars, marking))
    prob += expr <= n - 1, f"cut_forbid_{len(prob.constraints)}"


def _is_marking_in_bdd_expr(reach_expr, places: List[str], marking: np.ndarray) -> bool:
    assign = {
        exprvar(str(name)): int(bit)
        for name, bit in zip(places, marking.tolist())
    }
    reduced = reach_expr.restrict(assign)
    return reduced.is_one()


def _deadlock_reachable_marking_ilp(
    pn: PetriNet, reachable_bdd: BinaryDecisionDiagram
) -> Optional[List[int]]:
    prob, x_vars, places = _build_deadlock_ilp_model(pn)
    reach_expr = bdd2expr(reachable_bdd)

    while True:
        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        status_str = pulp.LpStatus.get(prob.status, None)

        if status_str not in ("Optimal", "Feasible"):
            return None

        marking = np.array([int(round(v.value())) for v in x_vars], dtype=int)

        if _is_marking_in_bdd_expr(reach_expr, places, marking):
            return [int(x) for x in marking.tolist()]

        _forbid_marking(prob, x_vars, marking)


def _deadlock_reachable_marking_bfs(
    pn: PetriNet, reachable_bdd: Optional[BinaryDecisionDiagram]
) -> Optional[List[int]]:
    """Giữ nguyên giải pháp BFS cũ như một phương án dự phòng."""

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

    M0 = M0.reshape(-1)
    num_places = M0.shape[0]

    if I.shape != O.shape:
        raise ValueError("I and O must have the same shape")

    r, c = I.shape
    if c == num_places:
        row_is_transition = True
        num_trans = r
    elif r == num_places:
        row_is_transition = False
        num_trans = c
    else:
        raise ValueError("Shape of I does not match number of places/transitions")

    def pre_vec(t_idx: int) -> np.ndarray:
        return I[t_idx, :] if row_is_transition else I[:, t_idx]

    def post_vec(t_idx: int) -> np.ndarray:
        return O[t_idx, :] if row_is_transition else O[:, t_idx]

    if hasattr(pn, "place_ids"):
        places = list(pn.place_ids)
    else:
        places = [f"p{i+1}" for i in range(num_places)]

    place_index = {name: idx for idx, name in enumerate(places)}

    def marking_satisfies_bdd(marking: np.ndarray) -> bool:
        if reachable_bdd is None:
            return True

        point = {}
        for var in reachable_bdd.support:
            vname = str(var)
            idx = place_index.get(vname, None)
            if idx is None:
                continue
            point[var] = int(marking[idx])

        if not point:
            return reachable_bdd.is_one()

        restricted = reachable_bdd.restrict(point)
        return restricted.is_one()

    def is_enabled(marking: np.ndarray, t_idx: int) -> bool:
        pre = pre_vec(t_idx)
        post = post_vec(t_idx)

        if np.any(marking < pre):
            return False

        new_marking = marking - pre + post
        if np.any(new_marking > 1):
            return False

        return True

    def fire(marking: np.ndarray, t_idx: int) -> np.ndarray:
        pre = pre_vec(t_idx)
        post = post_vec(t_idx)
        return marking - pre + post

    visited = set()
    q = deque()

    init_tuple = tuple(int(x) for x in M0.tolist())
    visited.add(init_tuple)
    q.append(M0)

    while q:
        M = q.popleft()

        if marking_satisfies_bdd(M):
            any_enabled = False
            for t_idx in range(num_trans):
                if is_enabled(M, t_idx):
                    any_enabled = True
                    break

            if not any_enabled:
                return [int(x) for x in M.tolist()]

        for t_idx in range(num_trans):
            if is_enabled(M, t_idx):
                M_next = fire(M, t_idx)
                key = tuple(int(x) for x in M_next.tolist())
                if key not in visited:
                    visited.add(key)
                    q.append(M_next)

    return None
