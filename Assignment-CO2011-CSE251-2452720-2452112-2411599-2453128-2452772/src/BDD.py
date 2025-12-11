import collections
from typing import Tuple
from pyeda.inter import *
from .PetriNet import PetriNet
import numpy as np
import time

def reorder_places_bfs(pn: PetriNet) -> list:
    """
    Automatic Variable Reordering using BFS.
    Groups related places (connected via transitions) together.
    """
    # 1. Build Adjacency Graph of Places
    adj = collections.defaultdict(set)
    
    if hasattr(pn, "I"): I = np.array(getattr(pn, "I"), dtype=int)
    else: I = np.array(getattr(pn, "pre"), dtype=int)
    if hasattr(pn, "O"): O = np.array(getattr(pn, "O"), dtype=int)
    else: O = np.array(getattr(pn, "post"), dtype=int)
    
    num_trans = I.shape[0] if I.shape[1] == len(pn.place_ids) else I.shape[1]
    row_is_trans = (I.shape[0] == num_trans)

    for t in range(num_trans):
        # Identify connected places for each transition
        if row_is_trans:
            inputs = np.where(I[t, :] > 0)[0]
            outputs = np.where(O[t, :] > 0)[0]
        else:
            inputs = np.where(I[:, t] > 0)[0]
            outputs = np.where(O[:, t] > 0)[0]
            
        # Connect inputs and outputs in the adjacency graph
        nodes = np.concatenate((inputs, outputs))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                adj[u].add(v)
                adj[v].add(u)

    # 2. BFS Traversal to determine new order
    visited = [False] * len(pn.place_ids)
    new_order_indices = []
    
    # Start BFS from the first place (usually f0 or p0)
    for start_node in range(len(pn.place_ids)):
        if not visited[start_node]:
            queue = collections.deque([start_node])
            visited[start_node] = True
            new_order_indices.append(start_node)
            
            while queue:
                u = queue.popleft()
                # Sort neighbors to ensure deterministic ordering
                neighbors = sorted(list(adj[u]))
                for v in neighbors:
                    if not visited[v]:
                        visited[v] = True
                        new_order_indices.append(v)
                        queue.append(v)
                        
    return [pn.place_ids[i] for i in new_order_indices]

def bdd_reachable(pn: PetriNet) -> Tuple[BinaryDecisionDiagram, int]:
    print("   [BDD] Starting Symbolic Reachability...")
    
    # 1. Prepare Data
    if hasattr(pn, "I"): I = np.array(getattr(pn, "I"), dtype=int)
    else: I = np.array(getattr(pn, "pre"), dtype=int)
    
    if hasattr(pn, "O"): O = np.array(getattr(pn, "O"), dtype=int)
    else: O = np.array(getattr(pn, "post"), dtype=int)
    
    if hasattr(pn, "M0"): M0 = np.array(getattr(pn, "M0"), dtype=int).reshape(-1)
    else: M0 = np.array(getattr(pn, "initial_marking"), dtype=int).reshape(-1)

    num_places = M0.shape[0]
    if O.shape != I.shape: raise ValueError("Shape mismatch")
    r, c = I.shape
    if c == num_places: 
        row_is_transition = True
        num_trans = r
    else: 
        row_is_transition = False
        num_trans = c

    def get_row(matrix, t_idx):
        return matrix[t_idx, :] if row_is_transition else matrix[:, t_idx]

    # --- OPTIMIZATION: VARIABLE REORDERING ---
    print("   [BDD] Optimizing variable order (BFS Reordering)...")
    # Get old order to map M0 later
    old_ids = getattr(pn, "place_ids", [f"p{i}" for i in range(num_places)])
    old_id_to_idx = {pid: i for i, pid in enumerate(old_ids)}
    
    # Get new optimized order
    new_places = reorder_places_bfs(pn)
    
    # Remap M0 to new order
    new_M0_list = []
    for pid in new_places:
        idx = old_id_to_idx[pid]
        new_M0_list.append(M0[idx])
    M0 = np.array(new_M0_list)
    
    places = new_places
    # ----------------------------------------

    # 2. Initialize BDD Variables
    print(f"   [BDD] Creating BDD variables for {num_places} places...")
    X_vars = [bddvar(str(p)) for p in places]
    
    # 3. Initial State (M0)
    init_lits = []
    for bit, x in zip(M0, X_vars):
        init_lits.append(x if int(bit) else ~x)
    
    if not init_lits: Reach = bddvar('1')
    else:
        Reach = init_lits[0]
        for lit in init_lits[1:]: Reach = Reach & lit
        
    Frontier = Reach

    # 4. Prepare Partitioned Transitions
    print(f"   [BDD] Analyzing {num_trans} transitions...")
    transitions_data = []
    
    # Map matrices I/O to new variable order
    new_idx_to_old_idx = [old_id_to_idx[pid] for pid in new_places]
    
    for t in range(num_trans):
        pre_t_raw = get_row(I, t)
        post_t_raw = get_row(O, t)
        
        # Remap rows
        pre_t = np.array([pre_t_raw[old_idx] for old_idx in new_idx_to_old_idx])
        post_t = np.array([post_t_raw[old_idx] for old_idx in new_idx_to_old_idx])
        
        idx_inputs = np.where(pre_t > 0)[0]
        idx_outputs = np.where(post_t > 0)[0]
        
        # Build Enable Condition
        pre_cond = []
        for idx in idx_inputs: pre_cond.append(X_vars[idx])
        for idx in idx_outputs:
            if pre_t[idx] == 0: pre_cond.append(~X_vars[idx])
        
        if not pre_cond: En_Expr = bddvar('1')
        else:
            expr_temp = pre_cond[0]
            for l in pre_cond[1:]: expr_temp &= l
            En_Expr = expr_temp

        # Build Update Logic
        vars_to_smooth = []
        update_lits = []
        for idx in idx_inputs:
            vars_to_smooth.append(X_vars[idx])
            update_lits.append(~X_vars[idx])
        for idx in idx_outputs:
            vars_to_smooth.append(X_vars[idx])
            update_lits.append(X_vars[idx])
            
        if not update_lits: Up_Expr = bddvar('1')
        else:
            expr_temp = update_lits[0]
            for l in update_lits[1:]: expr_temp &= l
            Up_Expr = expr_temp
            
        transitions_data.append({
            'enable': En_Expr,
            'smooth_vars': vars_to_smooth,
            'update': Up_Expr
        })

    # 5. Symbolic Loop
    print("   [BDD] Starting Fixed Point Iteration...")
    iter_count = 0
    start_loop = time.time()
    
    while True:
        iter_count += 1
        S_new_accum = None
        
        for t_data in transitions_data:
            S_en = Frontier & t_data['enable']
            if S_en.is_zero(): continue
            
            if t_data['smooth_vars']:
                S_core = S_en.smoothing(t_data['smooth_vars'])
            else:
                S_core = S_en
            S_next = S_core & t_data['update']
            
            if S_new_accum is None: S_new_accum = S_next
            else: S_new_accum |= S_next
            
        if S_new_accum is None: break
        New = S_new_accum & ~Reach
        if New.is_zero(): break
            
        Reach = Reach | New
        Frontier = New
        
        # print(f"      -> Iter {iter_count} finished.")

    elapsed = time.time() - start_loop
    print(f"   [BDD] Finished in {elapsed:.4f}s. Counting states...")
    
    count = int(Reach.satisfy_count())
    return Reach, count