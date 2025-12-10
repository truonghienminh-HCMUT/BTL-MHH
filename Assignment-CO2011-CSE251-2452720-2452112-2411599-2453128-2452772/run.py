from PetriNet import PetriNet
from src.BDD import bdd_reachable
from src.Optimization import max_reachable_marking
from src.BFS import bfs_reachable
from src.DFS import dfs_reachable
from src.Deadlock import deadlock_reachable_marking
from pyeda.inter import * 
import numpy as np
import time
from graphviz import Source
import sys

def generate_custom_bdd_image(bdd_obj):
    """
    Hàm này lấy đối tượng BDD từ PyEDA và vẽ ra ảnh.
    """
    try:
        # PyEDA có hàm .to_dot() để xuất cấu trúc đồ thị
        dot_code = bdd_obj.to_dot()
        
        # Tạo đối tượng Source của Graphviz
        s = Source(dot_code, filename="bdd", format="svg")
        
        # Render ra file ảnh
        output_path = s.render(cleanup=True)
        print(f"\n[SUCCESS] Đã vẽ BDD dựa trên dữ liệu tính toán.")
        print(f"File ảnh được lưu tại: {output_path}")
        
    except Exception as e:
        print(f"\n[ERROR] Không thể vẽ hình BDD thật. Lỗi: {e}")

def main():
    np.set_printoptions(threshold=sys.maxsize, linewidth=np.inf)

    # Bắt đầu tính tổng thời gian chạy chương trình
    total_start_time = time.time()
    # ------------------------------------------------------
    # 1. Load Petri Net từ file PNML
    # ------------------------------------------------------
    # Đảm bảo bạn đã tạo file deadlock.pnml
    filename = "testcase6.pnml"   
    print("Loading PNML:", filename)

    try:
        pn = PetriNet.from_pnml(filename)
        print("\n--- TASK 1: PNML PARSING ---")
        print(pn)
        print("\nTASK 1: [SUCCESS]")
    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR] Không tìm thấy file '{filename}'.")
        print("Vui lòng tạo file deadlock.pnml theo hướng dẫn trước đó.")
        return

    # ------------------------------------------------------
    # 2. BFS reachable
    # ------------------------------------------------------
    print("\n--- TASK 2: EXPLICIT REACHABILITY ---")
    print("\n---     BFS Reachable Markings    ---")

    start_bfs = time.perf_counter()  # [THÊM] Bắt đầu bấm giờ
    bfs_set = bfs_reachable(pn)
    end_bfs = time.perf_counter()    # [THÊM] Kết thúc bấm giờ
    
    bfs_time = end_bfs - start_bfs # Tính khoảng thời gian
    for m in bfs_set:
        print(np.array(m))
    print("Total BFS reachable =", len(bfs_set))

    # ------------------------------------------------------
    # 3. DFS reachable
    # ------------------------------------------------------
    print("\n---     DFS Reachable Markings    ---")
    dfs_set = dfs_reachable(pn)
    for m in dfs_set:
        print(np.array(m))
    print("Total DFS reachable =", len(dfs_set))
    print("\nTASK 2: [SUCCESS]")

    # ------------------------------------------------------
    # 4. BDD reachable
    # ------------------------------------------------------
    print("\n--- TASK 3: BDD-BASED REACHABILITY ---")
    try:
        start_bdd = time.perf_counter()  # [THÊM] Bắt đầu bấm giờ
        bdd, count = bdd_reachable(pn)
        end_bdd = time.perf_counter()    # [THÊM] Kết thúc bấm giờ
        
        bdd_time = end_bdd - start_bdd # Tính khoảng thời gian

        print("BDD reachable markings count =", count) 
        generate_custom_bdd_image(bdd) # Chỉ vẽ hình minh họa tĩnh
        print("\nTASK 3: [SUCCESS]")
    except Exception as e:
        print("Lỗi BDD:", e)
        return
    # ------------------------------------------------------
    # 5. Deadlock detection
    # ------------------------------------------------------
    print("\n--- TASK 4: ILP + BDD DEADLOCK DETECTION ---")
    dead = deadlock_reachable_marking(pn, bdd)
    if dead is not None:
        print("Deadlock marking:", dead)
        print("\nTASK 4: [SUCCESS]")
    else:
        print("No deadlock reachable.")

    # ------------------------------------------------------
    # 6. Optimization: maximize c·M
    # ------------------------------------------------------
    print("\n--- TASK 5: REACHABLE OPTIMIZATION ---")

    # [FIX 1] Tạo vector c khớp với số lượng Place thực tế
    num_places = len(pn.place_ids)
    
    # Vector mẫu của bạn (chỉ dùng nếu khớp số lượng)
    c_sample = np.array([1, -2, 3, -1, 1, 2])
    
    if num_places == len(c_sample):
        c = c_sample
    else:
        print(f"[WARN] File PNML có {num_places} places, nhưng vector c mẫu có {len(c_sample)}.")
        print("-> Tự động tạo vector c ngẫu nhiên để test.")
        np.random.seed(42)
        c = np.random.randint(-2, 3, size=num_places) # Random từ -2 đến 2
    
    print("Weight vector c:", c)

    # [FIX 2] Logic Mapping Chính xác (ID -> Name)
    uuid_map = {}
    
    # Map chính xác từ ID sang Name (dựa trên thứ tự parse trong PetriNet.py)
    # Vì pn.place_ids và pn.place_names có cùng thứ tự index
    if hasattr(pn, 'place_ids') and hasattr(pn, 'place_names'):
        for pid, pname in zip(pn.place_ids, pn.place_names):
            if pname: 
                uuid_map[pid] = pname
                # Fallback: Map thêm chữ thường/hoa để chắc chắn bắt được biến BDD
                uuid_map[pid.lower()] = pname
                uuid_map[pid.upper()] = pname
            else:
                # Nếu không có tên, map ID -> ID
                uuid_map[pid] = pid

    # print("DEBUG MAP:", uuid_map)

    try:
        # [FIX 3] Truyền pn.place_ids thay vì place_names để đảm bảo không bị None
        max_mark, max_val = max_reachable_marking(
            pn.place_ids,   # Dùng ID để duyệt
            bdd, 
            c, 
            place_uuid_mapping=uuid_map # Dùng Map để tìm tên biến trong BDD
        )
        print("Max marking found:", max_mark)
        print("Max value:", max_val)
        
    except TypeError as te:
        print(f"\n[LỖI PARAM] {te}")
        print("Hãy chắc chắn file src/Optimization.py đã được cập nhật hàm nhận tham số 'place_uuid_mapping'.")
    except Exception as e:
        print(f"\n[LỖI] Optimization thất bại: {e}")

    # Tổng kết toàn bộ thời gian chạy
    total_duration = time.time() - total_start_time
    print("-" * 30)
    print(f"PROGRAM FINISHED IN: {total_duration:.4f} seconds")

    print(f"Thời gian chạy BFS: {bfs_time:.6f} giây") # In ra kết quả

    print(f"Thời gian chạy BDD: {bdd_time:.6f} giây") # In ra kết quả

    # So sánh nhanh
    if bfs_time > 0:
        diff = bfs_time / bdd_time if bdd_time > 0 else 0
        print(f"=> BDD nhanh hơn BFS khoảng {diff:.2f} lần" if diff > 1 else f"=> BFS nhanh hơn BDD khoảng {1/diff:.2f} lần")

if __name__ == "__main__":
    main()