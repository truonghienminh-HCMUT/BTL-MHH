import pytest
from src.PetriNet import PetriNet
from pathlib import Path

def test_001():
    base_dir = Path(__file__).parent / "tests/test_1"
    
    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_002():
    base_dir = Path(__file__).parent / "tests/test_2"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_003():
    base_dir = Path(__file__).parent / "tests/test_3"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_004():
    base_dir = Path(__file__).parent / "tests/test_4"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_005():
    base_dir = Path(__file__).parent / "tests/test_5"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"

def test_006():
    base_dir = Path(__file__).parent / "tests/test_6"

    pn = PetriNet.from_pnml(str(base_dir / "example.pnml"))
    with open(base_dir / "expected.txt", "r", encoding="utf-8") as f:
        expected_content = f.read().strip()
        
    actual_content = str(pn).strip()
    assert actual_content == expected_content, "PetriNet.from_pnml output does not match expected"