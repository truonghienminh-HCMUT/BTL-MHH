from src.PetriNet import PetriNet
from src.BDD import bdd_reachable
from src.Optimization import max_reachable_marking
from src.BFS import bfs_reachable
from src.DFS import dfs_reachable
from src.Deadlock import deadlock_reachable_marking
from pyeda.inter import * 
import numpy as np
from graphviz import Source

def generate_custom_bdd_image():
    """
    Hàm này tạo ra file ảnh bdd_custom.png dựa trên cấu trúc cứng 
    được định nghĩa bằng ngôn ngữ DOT (mô phỏng hình ảnh bạn cung cấp).
    """
    dot_code = """
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

def main():
    # ------------------------------------------------------
    # 1. Load Petri Net từ file PNML
    # ------------------------------------------------------
    # Đảm bảo bạn đã tạo file deadlock.pnml
    filename = "example.pnml"   
    print("Loading PNML:", filename)

    try:
        pn = PetriNet.from_pnml(filename)
        print("\n--- Petri Net Loaded ---")
        print(pn)
    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR] Không tìm thấy file '{filename}'.")
        print("Vui lòng tạo file deadlock.pnml theo hướng dẫn trước đó.")
        return

    # ------------------------------------------------------
    # 2. BFS reachable
    # ------------------------------------------------------
    print("\n--- BFS Reachable Markings ---")
    bfs_set = bfs_reachable(pn)
    for m in bfs_set:
        print(np.array(m))
    print("Total BFS reachable =", len(bfs_set))

    # ------------------------------------------------------
    # 3. DFS reachable
    # ------------------------------------------------------
    print("\n--- DFS Reachable Markings ---")
    dfs_set = dfs_reachable(pn)
    for m in dfs_set:
        print(np.array(m))
    print("Total DFS reachable =", len(dfs_set))

    # ------------------------------------------------------
    # 4. BDD reachable
    # ------------------------------------------------------
    print("\n--- BDD Reachable ---")
    bdd, count = bdd_reachable(pn)
    print("BDD reachable markings =", count)
    
    print("\n--- Generating Custom BDD Image ---")
    generate_custom_bdd_image()

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

    # === [FIX FINAL] LOGIC MAPPING MẠNH MẼ ===
    uuid_map = {}
    
    # 1. Map trực tiếp từ danh sách nếu có
    if hasattr(pn, 'places') and hasattr(pn, 'place_names'):
        ids = [str(x) for x in pn.places]
        names = [str(x) for x in pn.place_names]
        if len(ids) == len(names):
            uuid_map = dict(zip(ids, names))

    # 2. Map dự phòng "Case Insensitive" (Quan trọng cho trường hợp p1 -> P1)
    # Duyệt qua tất cả các tên Place mong đợi (P1, P2...)
    # Tự động map 'p1' -> 'P1', 'p2' -> 'P2'
    if hasattr(pn, 'place_names'):
        for name in pn.place_names:
            # Map chính tên nó (P1 -> P1)
            uuid_map[name] = name 
            # Map chữ thường -> Chữ hoa (p1 -> P1)
            uuid_map[name.lower()] = name
            # Map chữ hoa -> Chữ hoa (P1 -> P1)
            uuid_map[name.upper()] = name
    
    # Debug: In ra map để kiểm tra
    # print("Debug UUID Map keys:", list(uuid_map.keys()))

    try:
        max_mark, max_val = max_reachable_marking(
            pn.place_names, 
            bdd, 
            c, 
            place_uuid_mapping=uuid_map
        )
        print("c:", c)
        print("Max marking:", max_mark)
        print("Max value:", max_val)
    except TypeError:
        print("\n[LỖI] Sai tham số. Hãy cập nhật src/Optimization.py theo hướng dẫn cũ.")
    except Exception as e:
        print(f"\n[LỖI] Optimization thất bại: {e}")

if __name__ == "__main__":
    main()