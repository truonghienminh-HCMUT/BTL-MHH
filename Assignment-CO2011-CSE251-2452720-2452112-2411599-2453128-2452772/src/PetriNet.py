import numpy as np
import xml.etree.ElementTree as ET
from typing import List, Optional

class PetriNet:
    def __init__(  
        self,
        place_ids: List[str],   # Danh sách ID của các Place và Transition
        trans_ids: List[str],
        place_names: List[Optional[str]],
        trans_names: List[Optional[str]],
        I: np.ndarray,  # Ma trận đầu vào (input)
        O: np.ndarray,  # Ma trận đầu ra (output)
        M0: np.ndarray  # Vector Marking ban đầu (trạng thái token ban đầu )
    ):
        self.place_ids = place_ids
        self.trans_ids = trans_ids
        self.place_names = place_names
        self.trans_names = trans_names
        self.I = I
        self.O = O
        self.M0 = M0

    @classmethod
    def from_pnml(cls, filename: str) -> "PetriNet":
        """
        Parse a PNML file and construct a PetriNet object.
        
        Args:
            filename: Path to the PNML file
            
        Returns:
            PetriNet object with parsed data
        """
        # Đọc file XML và xử lý namespace 
        tree = ET.parse(filename)
        root = tree.getroot()
        
        # Handle namespace if present
        ns = {'pnml': 'http://www.pnml.org/version-2009/grammar/pnml'} # chuẩn bị namespace
        
        # Tìm phần tử <net> trong trường hợp có và không có namespace
        net = root.find('.//pnml:net', ns)
        if net is None:
            net = root.find('.//net')
        if net is None:
            raise ValueError("No net element found in PNML file")
        
        # Tìm phần tử <page> bên trong <net>
        page = net.find('.//pnml:page', ns)
        if page is None:
            page = net.find('.//page')
        if page is None:
            page = net  
        
        # Parse places
        place_ids = []
        place_names = []
        place_map = {}  
        initial_marking = {}
        
        places = page.findall('.//pnml:place', ns)
        if not places:
            places = page.findall('.//place')
        
        # Quét và đánh chỉ số cho Place (Vị trí)
        for place in places:
            place_id = place.get('id')
            place_ids.append(place_id)
            place_map[place_id] = len(place_ids) - 1
            
            # Lấy tên place (nếu có)
            name_elem = place.find('.//pnml:name/pnml:text', ns)
            if name_elem is None:
                name_elem = place.find('.//name/text')
            
            place_name = name_elem.text if name_elem is not None else None
            place_names.append(place_name)
            
            # Thiết lập Marking ban đầu (nếu không có thì marking = 0)
            marking_elem = place.find('.//pnml:initialMarking/pnml:text', ns)
            if marking_elem is None:
                marking_elem = place.find('.//initialMarking/text')
            
            if marking_elem is not None:
                try:
                    initial_marking[place_id] = int(marking_elem.text)
                except ValueError:
                    initial_marking[place_id] = 0
            else:
                initial_marking[place_id] = 0
        
        # Parse transitions
        trans_ids = []
        trans_names = []
        trans_map = {}  
        
        transitions = page.findall('.//pnml:transition', ns)
        if not transitions:
            transitions = page.findall('.//transition')
        
        #Quét và đánh chỉ số cho Transition (Chuyển đổi)
        for trans in transitions:
            trans_id = trans.get('id')
            trans_ids.append(trans_id)
            trans_map[trans_id] = len(trans_ids) - 1
            
            # Lấy tên transition
            name_elem = trans.find('.//pnml:name/pnml:text', ns)
            if name_elem is None:
                name_elem = trans.find('.//name/text')
            
            trans_name = name_elem.text if name_elem is not None else None
            trans_names.append(trans_name)
         
        # Initialize matrices (transitions × places)
        n_places = len(place_ids)
        n_trans = len(trans_ids)

        # Khởi tạo Ma trận & Quét các Cung (Arcs)
        # Số hàng = số transition
        # Số cột = số place
        I = np.zeros((n_trans, n_places), dtype=int)
        O = np.zeros((n_trans, n_places), dtype=int)
        
        # Parse arcs để điền vào I và O
        # Một arc dạng:
        # Place -> Transition -> điền vào ma trận I
        # Transition -> Place -> điền vào ma trận O
            
        arcs = page.findall('.//pnml:arc', ns)
        if not arcs:
            arcs = page.findall('.//arc')
        
        for arc in arcs:
            source = arc.get('source')
            target = arc.get('target')
            
            # Tìm trọng số (arc weight) (nếu không có thì default is 1)
            weight_elem = arc.find('.//pnml:inscription/pnml:text', ns)
            if weight_elem is None:
                weight_elem = arc.find('.//inscription/text')
            
            weight = 1
            if weight_elem is not None:
                try:
                    weight = int(weight_elem.text)
                except ValueError:
                    weight = 1
            
            # Xác định hướng arc
            if source in place_map and target in trans_map:
                # Place to Transition: input arc
                place_idx = place_map[source]
                trans_idx = trans_map[target]
                I[trans_idx, place_idx] = weight
            elif source in trans_map and target in place_map:
                # Transition to Place: output arc
                trans_idx = trans_map[source]
                place_idx = place_map[target]
                O[trans_idx, place_idx] = weight
        
        # Tạo Vector Marking (M0)
        M0 = np.array([initial_marking.get(pid, 0) for pid in place_ids], dtype=int)
        
        # Trả về đối tượng Petri Net
        return cls(place_ids, trans_ids, place_names, trans_names, I, O, M0)

    def __str__(self) -> str:
        s = []
        s.append("Places: " + str(self.place_ids))
        s.append("Place names: " + str(self.place_names))
        s.append("\nTransitions: " + str(self.trans_ids))
        s.append("Transition names: " + str(self.trans_names))
        s.append("\nI (input) matrix:")
        s.append(str(self.I))
        s.append("\nO (output) matrix:")
        s.append(str(self.O))
        s.append("\nInitial marking M0:")
        s.append(str(self.M0))
        return "\n".join(s)


