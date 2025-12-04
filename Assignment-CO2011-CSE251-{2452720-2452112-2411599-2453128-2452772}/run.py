import os
import sys
import pytest
import numpy as np

# Import các module từ folder src
from src.PetriNet import PetriNet
from src.BFS import bfs_reachable
from src.DFS import dfs_reachable
from src.BDD import bdd_reachable
from src.Optimization import max_reachable_marking
from src.Deadlock import deadlock_reachable_marking

# -------------------------------------------------------------------------
# 1. HÀM HỖ TRỢ (GIỮ NGUYÊN LOGIC CŨ)
# -------------------------------------------------------------------------
def run_solver(pnml_path):
    """
    Hàm này chạy toàn bộ logic tính toán và trả về chuỗi kết quả (Actual).
    """
    try:
        # Load Petri Net
        pn = PetriNet.from_pnml(pnml_path)
        pn_struct = str(pn) # Lấy cấu trúc để so sánh phần đầu

        # Chạy thuật toán
        bfs_res = len(bfs_reachable(pn))
        dfs_res = len(dfs_reachable(pn))
        bdd_node, bdd_res = bdd_reachable(pn)
        
        deadlock_marking = deadlock_reachable_marking(pn, bdd_node)
        deadlock_status = "No deadlock" if deadlock_marking is None else str(deadlock_marking)

        # Optimization (Vector c cố định)
        num_places = len(pn.place_ids)
        c_sample = np.array([1, -2, 3, -1, 1, 2])
        if num_places == len(c_sample):
            c = c_sample
        else:
            c = np.ones(num_places, dtype=int)

        # Map ID -> Name
        uuid_map = {}
        if hasattr(pn, 'place_ids') and hasattr(pn, 'place_names'):
             for pid, pname in zip(pn.place_ids, pn.place_names):
                uuid_map[pid] = pname if pname else pid

        max_mark, max_val = max_reachable_marking(pn.place_ids, bdd_node, c, uuid_map)

        # Tạo chuỗi kết quả
        stats_lines = [
            f"BFS reachable: {bfs_res}",
            f"DFS reachable: {dfs_res}",
            f"BDD reachable: {bdd_res}",
            f"Deadlock: {deadlock_status}",
            f"Max value: {max_val}"
        ]
        
        # Kết hợp cấu trúc + thống kê
        full_output = f"{pn_struct.strip()}\n" + "\n".join(stats_lines)
        return full_output
    except Exception as e:
        return f"Error: {str(e)}"

def get_test_cases():
    """
    Quét thư mục 'tests/' để tìm danh sách các folder test_X.
    Trả về danh sách các tuple: [(tên_test, đường_dẫn), ...]
    """
    cases = []
    tests_dir = "tests" # Folder chứa các test case
    if os.path.exists(tests_dir):
        for f in os.listdir(tests_dir):
            path = os.path.join(tests_dir, f)
            # Chỉ lấy các folder bắt đầu bằng "test_"
            if os.path.isdir(path) and f.startswith("test_"):
                cases.append((f, path))
    
    # Sắp xếp theo tên (test_1, test_2...)
    cases.sort(key=lambda x: x[0])
    return cases

# -------------------------------------------------------------------------
# 2. HÀM TEST CHÍNH CỦA PYTEST
# -------------------------------------------------------------------------

# Dòng này sẽ tự động tạo ra nhiều test case tương ứng với số folder tìm được
@pytest.mark.parametrize("case_name, folder_path", get_test_cases())
def test(case_name, folder_path):
    """
    Pytest sẽ gọi hàm này với từng folder test tìm thấy.
    """
    print(f"\nExample: Đang chạy {case_name}...")
    
    pnml_file = os.path.join(folder_path, "example.pnml")
    expected_file = os.path.join(folder_path, "expected.txt")

    # Kiểm tra file input
    if not os.path.exists(pnml_file):
        pytest.fail(f"Không tìm thấy file example.pnml trong {case_name}")

    # Chạy tính toán
    actual_result = run_solver(pnml_file)

    # Nếu chưa có file expected thì báo SKIPPED (Bỏ qua) thay vì FAILED
    if not os.path.exists(expected_file):
        pytest.skip(f"Chưa có file expected.txt. Kết quả chạy:\n{actual_result}")

    # Đọc file expected
    with open(expected_file, 'r', encoding='utf-8') as f:
        expected_content = f.read().strip()

    # Chuẩn hóa (xóa khoảng trắng thừa, xử lý dòng Windows/Linux)
    actual_norm = actual_result.strip().replace('\r\n', '\n')
    expected_norm = expected_content.replace('\r\n', '\n')

    # So sánh (Assertion)
    # Nếu sai, Pytest sẽ tự in ra bảng so sánh chi tiết
    assert actual_norm == expected_norm, f"Kết quả không khớp ở {case_name}!"

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))