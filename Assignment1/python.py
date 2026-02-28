import os

# Language Definition for Rat26S
KEYWORDS = {
    "integer", "boolean", "real",
    "if", "otherwise", "fi",
    "while", "return",
    "read", "write",
    "function", "true", "false"
}

OPERATORS = {"==", "!=", "<=", "=>", "=", "+", "-", "*", "/", ">", "<"}
SEPARATORS = {"(", ")", "{", "}", ";", ",", "@"}

class IdentifierFSM:
    def __init__(self):
        self.current_state = '1'
        self.accepting_states = {'2', '4', '5', '6'}
        self.transition_table = {
            ('1', 'letter'): '2', ('2', 'letter'): '4', ('2', 'digit'): '5', ('2', '_'): '6',
            ('4', 'letter'): '4', ('4', 'digit'): '5', ('4', '_'): '6',
            ('5', 'letter'): '4', ('5', 'digit'): '5', ('5', '_'): '6',
            ('6', 'letter'): '4', ('6', 'digit'): '5', ('6', '_'): '6',
        }

    def next_state(self, char):
        input_type = None
        if char.isalpha(): input_type = 'letter'
        elif char.isdigit(): input_type = 'digit'
        elif char == '_': input_type = '_'
        
        state = self.transition_table.get((self.current_state, input_type))
        return state if state else 'reject'

class IntegerFSM:
    def __init__(self):
        self.current_state = '1'
        self.accepting_states = {'2'}
        self.transition_table = {
            ('1', 'digit'): '2', ('2', 'digit'): '2'
        }

    def next_state(self, char):
        input_type = 'digit' if char.isdigit() else None
        state = self.transition_table.get((self.current_state, input_type))
        return state if state else 'reject'

class RealFSM:
    def __init__(self):
        self.current_state = '1'
        self.accepting_states = {'4'}
        self.transition_table = {
            ('1', 'digit'): '2', ('2', 'digit'): '2', ('2', '.'): '3',
            ('3', 'digit'): '4', ('4', 'digit'): '4',
        }

    def next_state(self, char):
        input_type = 'digit' if char.isdigit() else ('.' if char == '.' else None)
        state = self.transition_table.get((self.current_state, input_type))
        return state if state else 'reject'

def lexer(content):
    content += " " # EOF padding
    char_pointer = 0
    length = len(content)
    tokens_and_lexemes = []

    while char_pointer < length:
        # Skip Whitespace
        if content[char_pointer].isspace():
            char_pointer += 1
            continue

        # Skip Comments /* ... */
        if content[char_pointer] == "/" and char_pointer + 1 < length and content[char_pointer + 1] == "*":
            char_pointer += 2
            while char_pointer + 1 < length:
                if content[char_pointer] == "*" and content[char_pointer + 1] == "/":
                    char_pointer += 2
                    break
                char_pointer += 1
            continue

        # 1. Match two-character operators
        if char_pointer + 1 < length:
            two_char = content[char_pointer : char_pointer + 2]
            if two_char in OPERATORS:
                tokens_and_lexemes.append(("operator", two_char))
                char_pointer += 2
                continue

        # 2. Match single-character operators and separators
        one_char = content[char_pointer]
        if one_char in SEPARATORS:
            tokens_and_lexemes.append(("separator", one_char))
            char_pointer += 1
            continue
        if one_char in OPERATORS:
            tokens_and_lexemes.append(("operator", one_char))
            char_pointer += 1
            continue

        # 3. Match Identifiers/Keywords and Numbers using FSMs (Greedy)
        id_fsm = IdentifierFSM()
        int_fsm = IntegerFSM()
        real_fsm = RealFSM()
        
        last_valid_type = None
        last_valid_lexeme = ""
        
        current_id_lexeme = ""
        current_int_lexeme = ""
        current_real_lexeme = ""
        
        temp_ptr = char_pointer
        while temp_ptr < length:
            c = content[temp_ptr]
            any_active = False
            
            # Identifier FSM
            if id_fsm.current_state != 'reject':
                next_s = id_fsm.next_state(c)
                if next_s != 'reject':
                    id_fsm.current_state = next_s
                    current_id_lexeme += c
                    if id_fsm.current_state in id_fsm.accepting_states:
                        if len(current_id_lexeme) >= len(last_valid_lexeme):
                            last_valid_type = "keyword" if current_id_lexeme in KEYWORDS else "identifier"
                            last_valid_lexeme = current_id_lexeme
                    any_active = True
                else: id_fsm.current_state = 'reject'
            
            # Integer FSM
            if int_fsm.current_state != 'reject':
                next_s = int_fsm.next_state(c)
                if next_s != 'reject':
                    int_fsm.current_state = next_s
                    current_int_lexeme += c
                    if int_fsm.current_state in int_fsm.accepting_states:
                        if len(current_int_lexeme) >= len(last_valid_lexeme):
                            last_valid_type = "integer"
                            last_valid_lexeme = current_int_lexeme
                    any_active = True
                else: int_fsm.current_state = 'reject'
                
            # Real FSM
            if real_fsm.current_state != 'reject':
                next_s = real_fsm.next_state(c)
                if next_s != 'reject':
                    real_fsm.current_state = next_s
                    current_real_lexeme += c
                    if real_fsm.current_state in real_fsm.accepting_states:
                        if len(current_real_lexeme) >= len(last_valid_lexeme):
                            last_valid_type = "real"
                            last_valid_lexeme = current_real_lexeme
                    any_active = True
                else: real_fsm.current_state = 'reject'
            
            if not any_active:
                break
            temp_ptr += 1

        if last_valid_type:
            tokens_and_lexemes.append((last_valid_type, last_valid_lexeme))
            char_pointer += len(last_valid_lexeme)
        else:
            # Illegal character
            if char_pointer < length - 1:
                tokens_and_lexemes.append(("invalid", content[char_pointer]))
            char_pointer += 1

    return tokens_and_lexemes

def main():
    output_folder = "output_results"
    os.makedirs(output_folder, exist_ok=True)

    while True:
        print("\n" + "="*30)
        print("Rat26S Lexical Analyzer (Final FSM)")
        print("="*30)
        print("1) Run Preset Test 1 (test1.txt)")
        print("2) Run Preset Test 2 (test2.txt)")
        print("3) Run Preset Test 3 (test3.txt)")
        print("C) Run Custom .rat25 file")
        print("Q) Quit")
        
        choice = input("\nSelection: ").strip().lower()
        if choice == 'q': break
        
        if choice in ['1', '2', '3']:
            input_file = f"test{choice}.txt" 
            output_filename = f"output{choice}.out" 
        elif choice == 'c':
            input_file = input("Enter filename (e.g., mysource.rat25): ").strip()
            if not input_file.endswith(".rat25"):
                print("Error: File must end with .rat25")
                continue
            output_filename = input_file.replace(".rat25", ".out")
        else:
            print("Invalid selection.")
            continue

        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found.")
            continue

        full_output_path = os.path.join(output_folder, output_filename)

        try:
            with open(input_file, 'r') as f:
                content = f.read()
            
            tokens = lexer(content)
            
            with open(full_output_path, 'w') as out:
                out.write(f"{'token':<15} {'lexeme':<15}\n")
                out.write("-" * 30 + "\n")
                for t_type, lex in tokens:
                    out.write(f"{t_type:<15} {lex:<15}\n")
            
            print(f"Success! Output saved to: {full_output_path}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
