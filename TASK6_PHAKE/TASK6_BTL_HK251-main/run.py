from src.PetriNet import PetriNet
from src.BDD import bdd_reachable
from src.Optimization import max_reachable_marking
from src.BFS import bfs_reachable
from src.DFS import dfs_reachable
from src.Deadlock import deadlock_reachable_marking
from pyeda.inter import * 
import numpy as np

def main():
   # ------------------------------------------------------
    # 1. Load Petri Net từ file PNML
    # ------------------------------------------------------
    filename = "example.pnml"
    print(f"Loading PNML: {filename}")

    pn = PetriNet.from_pnml(filename)
    print("\n--- Petri Net Structure ---")
    print(f"Places ({len(pn.place_ids)}):")
    p_ids = getattr(pn, 'place_ids', []) 
    p_names = getattr(pn, 'place_names', [])
    for name, pid in zip(p_names, p_ids):
        print(f"  - {name} : {pid}")
    t_ids = getattr(pn, 'transition_ids', getattr(pn, 'transitions', []))
    t_names = getattr(pn, 'transition_names', [])
    
    print(f"\nTransitions ({len(t_ids)}):")
    for name, tid in zip(t_names, t_ids):
        print(f"  - {name} : {tid}")
        
    print("-" * 30)

    # ------------------------------------------------------
    # 2. BFS reachable
    # ------------------------------------------------------
    print("\n--- BFS Reachable Markings ---")
    bfs_set = bfs_reachable(pn)
    print("Total BFS reachable =", len(bfs_set))

    # ------------------------------------------------------
    # 3. DFS reachable
    # ------------------------------------------------------
    print("\n--- DFS Reachable Markings ---")
    dfs_set = dfs_reachable(pn)
    print("Total DFS reachable =", len(dfs_set))

    # ------------------------------------------------------
    # 4. BDD reachable
    # ------------------------------------------------------
    print("\n--- BDD Reachable ---")
    bdd, count = bdd_reachable(pn)
    print("BDD reachable markings =", count)

    # ------------------------------------------------------
    # 5. Deadlock detection
    # ------------------------------------------------------
    print("\n--- Deadlock reachable marking ---")
    dead = deadlock_reachable_marking(pn, bdd)
    if dead is not None:
        print("Deadlock marking:", dead)
    else:
        print("No deadlock reachable.")

    # ------------------------------------------------------
    # 6. Optimization: maximize c·M
    # ------------------------------------------------------
    c = np.array([1, -2, 3, -1, 1, 2])
    print("\n--- Optimize c·M ---")
    place_ids = pn.place_ids
    if len(c) != len(place_ids):
        print(f"Warning: Vector c ({len(c)}) không khớp số lượng place ({len(place_ids)}). Auto resize.")
        c = np.resize(c, len(place_ids))

    max_mark, max_val = max_reachable_marking(
        place_ids, bdd, c
    )
    print("c:", c)
    print("Max marking:", max_mark)
    print("Max value:", max_val)


if __name__ == "__main__":
    main()