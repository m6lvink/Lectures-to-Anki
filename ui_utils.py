def selectCardType():
    print("\n--- Card Type ---")
    print("1. Cloze (fill-in-the-blank)")
    print("2. Basic (front/back)")
    
    while True:
        choice = input("Choice [1/2]: ").strip() or "1"
        if choice == "1":
            return "Cloze"
        elif choice == "2":
            return "Basic"
        print("Enter 1 or 2")

def selectThinkingMode():
    print("\n--- Processing Mode ---")
    print("Regular: faster, cheaper")
    print("Thinking: slower, better quality")
    
    while True:
        choice = input("Use thinking mode? [y/n]: ").strip().lower()
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no", ""):
            return False
        print("Enter y or n")

def selectOutputMode():
    print("\n--- Output Mode ---")
    print("1. Separate files (one CSV per document)")
    print("2. Combined file (single CSV with tags)")
    
    while True:
        choice = input("Choice [1/2]: ").strip() or "1"
        if choice == "1":
            return "separate"
        elif choice == "2":
            return "combined"
        print("Enter 1 or 2")
