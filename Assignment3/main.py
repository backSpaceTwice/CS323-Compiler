import os
import sys

# Ensure the current script directory is in the path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
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
    # Determine the actual path to the file
    actual_path = file_path
    if not os.path.exists(actual_path):
        # Try relative to script directory if not found
        potential_path = os.path.join(script_dir, os.path.basename(file_path))
        if os.path.exists(potential_path):
            actual_path = potential_path
        else:
            print(f"Error: File '{file_path}' not found at any known location.", file=sys.stderr)
            return

    output_folder = os.path.join(script_dir, "output_results")
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
