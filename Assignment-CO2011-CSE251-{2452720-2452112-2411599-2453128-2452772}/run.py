import os
import sys
from pathlib import Path

import numpy as np
import pytest

# ================== IMPORT MODULES CHÍNH ==================
from src.PetriNet import PetriNet
from src.BFS import bfs_reachable
from src.DFS import dfs_reachable
from src.BDD import bdd_reachable
from src.Optimization import max_reachable_marking
from src.Deadlock import deadlock_reachable_marking

from graphviz import Source  # dùng để vẽ BDD (demo)


# ======================================================================
# 1. HÀM CHÍNH DÙNG CHO TEST – TRẢ VỀ STRING ĐỂ SO VỚI expected.txt
# ======================================================================
def run_solver(pnml_path: str) -> str:
    """
    Load PNML -> tính BFS / DFS / BDD / Deadlock / Optimization
    -> trả về một chuỗi duy nhất để so sánh với expected.txt
    (KHÔNG in ra màn hình, để pytest dùng).
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
        if num_places == len(c_sample):
            c = c_sample
        else:
            c = np.ones(num_places, dtype=int)

        uuid_map = {}
        if hasattr(pn, "place_ids") and hasattr(pn, "place_names"):
            for pid, pname in zip(pn.place_ids, pn.place_names):
                uuid_map[pid] = pname if pname else pid

        max_mark, max_val = max_reachable_marking(pn.place_ids, bdd_node, c, uuid_map)

        lines = [
            pn_struct,
            f"BFS reachable: {bfs_res}",
            f"DFS reachable: {dfs_res}",
            f"BDD reachable: {bdd_res}",
            f"Deadlock: {deadlock_str}",
            f"Max value: {max_val}",
        ]
        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


# ======================================================================
# 2. QUÉT FOLDER tests/test_X ĐỂ TẠO TEST CASE CHO PYTEST
# ======================================================================
def get_test_cases():
    """
    Tìm tất cả folder tests/test_X có example.pnml + expected.txt
    Trả về list tuples: (tên_case, path_pnml, path_expected)
    """
    base = Path(__file__).parent / "tests"
    cases = []

    if base.exists():
        for folder in sorted(base.iterdir(), key=lambda p: p.name):
            if folder.is_dir() and folder.name.startswith("test_"):
                pnml = folder / "example.pnml"
                expected = folder / "expected.txt"
                if pnml.exists() and expected.exists():
                    cases.append((folder.name, str(pnml), str(expected)))

    return cases


# ======================================================================
# 3. TEST CHÍNH CHO PYTEST – DÙNG run_solver()
# ======================================================================
@pytest.mark.parametrize("case_name, pnml_path, expected_path", get_test_cases())
def test_examples_from_folders(case_name, pnml_path, expected_path):
    """
    Mỗi folder test_X được so sánh:
        actual = run_solver(example.pnml)
        expected = nội dung expected.txt
    """
    actual = run_solver(pnml_path).strip()
    with open(expected_path, "r", encoding="utf-8") as f:
        expected = f.read().strip()

    # Chuẩn hóa xuống dòng
    actual_norm = actual.replace("\r\n", "\n").strip()
    expected_norm = expected.replace("\r\n", "\n").strip()

    assert actual_norm == expected_norm, f"Kết quả không khớp ở {case_name}"


# ======================================================================
# 4. HÀM VẼ HÌNH BDD (DEMO) – GỘP TỪ FILE BẠN GỬI
# ======================================================================
def generate_custom_bdd_image():
    """
    Hàm này tạo file bdd.svg (BDD vẽ cứng theo DOT)
    – dùng cho DEMO, không liên quan tới chấm điểm.
    """
    dot_code = r"""
    digraph BDD {
        rankdir=TB;
        nodesep=0.5;
        ranksep=0.5;
        splines=true;
        node [shape=circle, fixedsize=true, width=0.6, fontsize=12, fontname="Helvetica"];
        
        {
            node [shape=box, width=0.8, height=0.4];
            T1 [label="1"];
            T0 [label="0"];
        }

        N1 [label="P1"];
        N2_L [label="P2"]; N2_R [label="P2"];
        N3_L [label="P3"]; N3_M [label="P3"]; N3_R [label="P3"];
        N4_L [label="P4"]; N4_M [label="P4"]; N4_R [label="P4"];
        N5_L [label="P5"]; N5_M1 [label="P5"]; N5_M2 [label="P5"]; N5_R [label="P5"];
        N6_R [label="P6"];

        edge [style=solid]; N1 -> N2_L [label="1"];
        edge [style=dashed]; N1 -> N2_R [label="0"];

        edge [style=solid]; N2_L -> N3_L [label="1"];
        edge [style=dashed]; N2_L -> N3_M [label="0"];

        edge [style=solid]; N2_R -> N3_R [label="1"];
        edge [style=dashed]; N2_R -> T1 [label="0"];

        edge [style=solid]; N3_L -> N4_L [label="1"];
        edge [style=dashed]; N3_L -> T1 [label="0"];

        edge [style=solid]; N3_M -> T1 [label="1"];
        edge [style=dashed]; N3_M -> N5_L [label="0"];

        edge [style=solid]; N3_R -> N4_M [label="1"];
        edge [style=dashed]; N3_R -> N4_R [label="0"];

        edge [style=solid]; N4_L -> T1 [label="1"];
        edge [style=dashed]; N4_L -> T1 [label="0"];

        edge [style=solid]; N4_M -> T1 [label="1"];
        edge [style=dashed]; N4_M -> N5_M1 [label="0"];

        edge [style=solid]; N4_R -> N5_M2 [label="1"];
        edge [style=dashed]; N4_R -> N5_R [label="0"];

        edge [style=solid]; N5_L -> T1 [label="1"];
        edge [style=dashed]; N5_L -> T1 [label="0"];

        edge [style=solid]; N5_M1 -> T1 [label="1"];
        edge [style=dashed]; N5_M1 -> N5_M2 [label="0"];

        edge [style=solid]; N5_M2 -> T1 [label="1"];
        edge [style=dashed]; N5_M2 -> T0 [label="0"];

        edge [style=solid]; N5_R -> T1 [label="1"];
        edge [style=dashed]; N5_R -> N6_R [label="0"];

        edge [style=solid]; N6_R -> T1 [label="1"];
        edge [style=dashed]; N6_R -> T0 [label="0"];

        { rank=same; N1; }
        { rank=same; N2_L; N2_R; }
        { rank=same; N3_L; N3_M; N3_R; }
        { rank=same; N4_L; N4_M; N4_R; }
        { rank=same; N5_L; N5_M1; N5_M2; N5_R; }
        { rank=same; N6_R; }
        { rank=same; T0; T1; }
    }
    """
    try:
        s = Source(dot_code, filename="bdd", format="svg")
        output_path = s.render(cleanup=True)
        print(f"\n[SUCCESS] Đã vẽ và lưu ảnh BDD tại: {output_path}")
    except Exception as e:
        print(f"\n[ERROR] Không thể vẽ hình. Lỗi: {e}")


# ======================================================================
# 5. CHẾ ĐỘ DEMO (CHẠY THỦ CÔNG, GIỐNG FILE BẠN GỬI)
# ======================================================================
def run_demo(filename: str = "example.pnml"):
    """
    Chế độ DEMO:
      - Load PNML
      - In Petri Net
      - In BFS/DFS reachable markings
      - Tính BDD + in số reachable
      - Vẽ hình BDD tĩnh (DOT)
      - Tính Deadlock và Max c·M
    Không dùng trong pytest.
    """
    print("Loading PNML:", filename)

    try:
        pn = PetriNet.from_pnml(filename)
        print("\n--- Petri Net Loaded ---")
        print(pn)
    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR] Không tìm thấy file '{filename}'.")
        return

    # BFS
    print("\n--- BFS Reachable Markings ---")
    bfs_set = bfs_reachable(pn)
    for m in bfs_set:
        print(np.array(m))
    print("Total BFS reachable =", len(bfs_set))

    # DFS
    print("\n--- DFS Reachable Markings ---")
    dfs_set = dfs_reachable(pn)
    for m in dfs_set:
        print(np.array(m))
    print("Total DFS reachable =", len(dfs_set))

    # BDD
    print("\n--- BDD Reachable ---")
    bdd, count = bdd_reachable(pn)
    print("BDD reachable markings =", count)

    print("\n--- Generating Custom BDD Image (static DOT) ---")
    generate_custom_bdd_image()

    # Deadlock
    print("\n--- Deadlock reachable marking ---")
    dead = deadlock_reachable_marking(pn, bdd)
    if dead is not None:
        print("Deadlock marking:", dead)
    else:
        print("No deadlock reachable.")

    # Optimization
    # ------------------------------------------------------
    # 6. Optimization: maximize c·M
    # ------------------------------------------------------
    print("\n--- Optimize c·M ---")

    # Vector mẫu (giống bạn)
    c_sample = np.array([1, -2, 3, -1, 1, 2])
    num_places = len(pn.place_ids)

    if num_places == len(c_sample):
        c = c_sample
    else:
        # fallback đơn giản: toàn 1
        c = np.ones(num_places, dtype=int)

    try:
        # DÙNG place_ids (UUID) y như trong test_Optimization,
        # KHÔNG truyền mapping để tránh lỗi
        max_mark_uuid, max_val = max_reachable_marking(
            pn.place_ids,  # ví dụ: ['4ae9...', 'c5dd...', ...]
            bdd,
            c
        )

        print("c:", c)
        print("Max value:", max_val)

        # In marking nhưng label theo P1, P2, P3
        pretty_parts = []
        for idx, token in enumerate(max_mark_uuid):
            # ưu tiên dùng tên place (P1, P2, P3), nếu None thì dùng UUID
            name = pn.place_names[idx] if pn.place_names[idx] is not None else pn.place_ids[idx]
            pretty_parts.append(f"{name}:{token}")

        print("Max marking (by place names): [" + ", ".join(pretty_parts) + "]")

    except Exception as e:
        print("\n[LỖI] Optimization thất bại:", e)



# ======================================================================
# 6. ENTRY POINT
# ======================================================================
if __name__ == "__main__":
    # Chạy DEMO khi gọi:  py run.py
    # Nếu bạn muốn file khác: py run.py other_example.pnml
    if len(sys.argv) > 1:
        run_demo(sys.argv[1])
    else:
        run_demo()
