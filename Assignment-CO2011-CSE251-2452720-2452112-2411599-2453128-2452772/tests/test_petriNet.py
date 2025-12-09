import pytest
from src.PetriNet import PetriNet
from pathlib import Path

def test_001():
    base_dir = Path(__file__).parent / "test_1_petriNet"
    
    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_002():
    base_dir = Path(__file__).parent / "test_2_petriNet"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_003():
    base_dir = Path(__file__).parent / "test_3_petriNet"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_004():
    base_dir = Path(__file__).parent / "test_4_petriNet"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_005():
    base_dir = Path(__file__).parent / "test_5_petriNet"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_006():
    base_dir = Path(__file__).parent / "test_6_petriNet"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"