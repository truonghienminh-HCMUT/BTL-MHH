from src.PetriNet import PetriNet


if __name__ == "__main__":
    pn = PetriNet.from_pnml("4.xml")
    print(pn)