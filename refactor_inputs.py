def refactor():
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        with open('main.py', 'w', encoding='utf-8') as f:
            for i, line in enumerate(lines):
                # Line 39 (1-based) is inside safe_input definition: val = input(prompt_text)
                # We skip replacement on this line.
                # Note: safe_input was added recently, line number from findstr was 39.
                # Double check content just in case.
                
                if "val = input(prompt_text)" in line or "def safe_input" in line:
                    f.write(line)
                else:
                    # check for input(
                    if "input(" in line:
                         # Replace strictly input( with safe_input(
                         # Avoid replacing safe_input( if it already exists (from my previous edit)
                         if "safe_input(" not in line:
                             line = line.replace("input(", "safe_input(")
                    f.write(line)
        print("Refactor complete.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    refactor()
