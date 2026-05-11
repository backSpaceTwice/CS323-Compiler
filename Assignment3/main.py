import os
import sys

# Determine the base directory for file operations
if getattr(sys, 'frozen', False):
    # Running as a compiled EXE (e.g., PyInstaller)
    base_dir = os.path.dirname(sys.executable)
    # The script/modules themselves are in _MEIPASS
    script_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    # Running as a normal Python script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = base_dir

# Ensure the current script directory is in the path for imports
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from lexer import lexer
    from parser import Parser
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def run_test_on_file(file_path):
    """
    Runs the parser on a single file and prints tables to console.
    """
    # Try multiple locations to find the source file
    locations_to_check = [
        file_path,                                  # Relative to current working directory
        os.path.join(base_dir, file_path),          # Relative to EXE/Script directory
        os.path.join(base_dir, os.path.basename(file_path)) # Just the filename in base directory
    ]

    actual_path = None
    for loc in locations_to_check:
        if os.path.exists(loc):
            actual_path = loc
            break

    if actual_path is None:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        return

    # Results should always go next to the executable
    output_folder = os.path.join(base_dir, "output_results")
    os.makedirs(output_folder, exist_ok=True)

    base_name = os.path.basename(actual_path)
    output_filename = os.path.join(output_folder, os.path.splitext(base_name)[0] + ".out")

    try:
        with open(actual_path, 'r') as f:
            source_code = f.read()
        
        tokens = lexer(source_code)
        
        parser = Parser(tokens, print_switch=True)
        success, _ = parser.parse(output_filename)

        if success:
            print(parser.instr_table.print_table())
            print(parser.sym_table.print_table())
        else:
            print(f"\nFAILED: {base_name} - See {output_filename} for details.", file=sys.stderr)
            
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}", file=sys.stderr)
    
    sys.stdout.flush()


if __name__ == '__main__':
    while True:
        print("\n" + "=" * 30)
        print("Rat26S Compiler - Assignment 3")
        print("=" * 30)
        print("1) Run Preset Test 1 (test1.rat26)")
        print("2) Run Preset Test 2 (test2.rat26)")
        print("3) Run Preset Test 3 (test3.rat26)")
        print("C) Run Custom file")
        print("Q) Quit")
        sys.stdout.flush()

        try:
            choice = input("\nSelection: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if choice == 'q':
            break

        filename = ""
        if choice == '1':
            filename = "test1.rat26"
        elif choice == '2':
            filename = "test2.rat26"
        elif choice == '3':
            filename = "test3.rat26"
        elif choice == 'c':
            filename = input("Enter the filename to test: ").strip()
        else:
            if choice:
                print(f"Invalid selection: '{choice}'")
            continue

        if filename:
            run_test_on_file(filename)
