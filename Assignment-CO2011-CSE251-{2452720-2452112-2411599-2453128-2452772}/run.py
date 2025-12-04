import os
import sys
import pytest
import numpy as np
from pathlib import Path

# ========== IMPORT MODULES ==========
from src.PetriNet import PetriNet
from src.BFS import bfs_reachable
from src.DFS import dfs_reachable
from src.BDD import bdd_reachable
from src.Optimization import max_reachable_marking
from src.Deadlock import deadlock_reachable_marking


# =====================================================================================
# 1. HÀM CHÍNH DÙNG CHO TEST – TRẢ VỀ OUTPUT CHUẨN (KHÔNG IN RA)
# =====================================================================================
def run_solver(pnml_path: str) -> str:
    """
    Load PNML → tính BFS / DFS / BDD / Deadlock / Optimization
    → trả về chuỗi để so sánh với expected.txt
    """
    try:
        pn = PetriNet.from_pnml(pnml_path)
        pn_struct = str(pn).strip()

        # BFS / DFS / BDD
        bfs_res = len(bfs_reachable(pn))
        dfs_res = len(dfs_reachable(pn))
        bdd_node, bdd_res = bdd_reachable(pn)

        # Deadlock
        deadlock_marking = deadlock_reachable_marking(pn, bdd_node)
        deadlock_str = "No deadlock" if deadlock_marking is None else str(deadlock_marking)

        # Optimization
        num_places = len(pn.place_ids)
        c_sample = np.array([1, -2, 3, -1, 1, 2])
        c = c_sample if num_places == len(c_sample) else np.ones(num_places, dtype=int)

        uuid_map = {}
        for pid, pname in zip(pn.place_ids, pn.place_names):
            uuid_map[pid] = pname if pname else pid

        max_mark, max_val = max_reachable_marking(pn.place_ids, bdd_node, c, uuid_map)

        output = [
            pn_struct,
            f"BFS reachable: {bfs_res}",
            f"DFS reachable: {dfs_res}",
            f"BDD reachable: {bdd_res}",
            f"Deadlock: {deadlock_str}",
            f"Max value: {max_val}",
        ]
        return "\n".join(output)

    except Exception as e:
        return f"Error: {str(e)}"


# =====================================================================================
# 2. QUÉT FOLDER test_X
# =====================================================================================
def get_test_cases():
    base = Path(__file__).parent / "tests"
    cases = []

    for folder in sorted(base.iterdir()):
        if folder.is_dir() and folder.name.startswith("test_"):
            pnml = folder / "example.pnml"
            expected = folder / "expected.txt"
            if pnml.exists() and expected.exists():
                cases.append((folder.name, str(pnml), str(expected)))

    return cases


# =====================================================================================
# 3. TÍCH HỢP PYTEST: dùng run_solver() để test
# =====================================================================================

@pytest.mark.parametrize("case_name, pnml_path, expected_path", get_test_cases())
def test_examples_from_folders(case_name, pnml_path, expected_path):
    actual = run_solver(pnml_path)
    with open(expected_path, "r", encoding="utf-8") as f:
        expected = f.read().strip()

    assert actual.strip() == expected.replace("\r\n", "\n").strip(), \
        f"Kết quả không khớp ở {case_name}"


# =====================================================================================
# 4. CHẾ ĐỘ DEMO (giống file bạn gửi)
# =====================================================================================

def run_demo(filename="example.pnml"):
    """
    CHẾ ĐỘ DEMO: Chạy full pipeline và in ra giống file bạn gửi.
    Không dùng trong pytest.
    """
    print("Loading PNML:", filename)
    try:
        pn = PetriNet.from_pnml(filename)
    except FileNotFoundError:
        print("Không tìm thấy file:", filename)
        return

    print("\n================= PETRI NET =================")
    print(pn)

    print("\n================= BFS =================")
    bfs_set = bfs_reachable(pn)
    for m in bfs_set:
        print(np.array(m))
    print("Total BFS reachable =", len(bfs_set))

    print("\n================= DFS =================")
    dfs_set = dfs_reachable(pn)
    for m in dfs_set:
        print(np.array(m))
    print("Total DFS reachable =", len(dfs_set))

    print("\n================= BDD =================")
    bdd, count = bdd_reachable(pn)
    print("BDD reachable markings count =", count)

    print("\n================= DEADLOCK =================")
    dead = deadlock_reachable_marking(pn, bdd)
    print("Deadlock:", dead if dead is not None else "No deadlock")

    print("\n================= OPTIMIZATION =================")
    num_places = len(pn.place_ids)
    c_sample = np.array([1, -2, 3, -1, 1, 2])
    c = c_sample if num_places == len(c_sample) else np.ones(num_places, dtype=int)
    uuid_map = {pid: (pname if pname else pid) for pid, pname in zip(pn.place_ids, pn.place_names)}

    max_mark, max_val = max_reachable_marking(pn.place_ids, bdd, c, uuid_map)
    print("Max marking:", max_mark)
    print("Max value:", max_val)


# =====================================================================================
# 5. MAIN ENTRY
# =====================================================================================
if __name__ == "__main__":
    # Nếu chạy Python trực tiếp → chạy DEMO
    # Nếu chạy pytest → pytest sẽ tự động dùng test_examples_from_folders()
    run_demo()
