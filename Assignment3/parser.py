import sys
import os


class SymbolTable:

    def __init__(self):
        self._table = {}
        self._memory_address = 10000

    def insert(self, lexeme, var_type):
        if lexeme in self._table:
            raise SemanticError(f"Error: '{lexeme}' has already been declared.")
        self._table[lexeme] = {
            "address": self._memory_address,
            "type": var_type,
        }
        self._memory_address += 1

    def lookup(self, lexeme):
        return self._table.get(lexeme)

    def get_address(self, lexeme):
        entry = self.lookup(lexeme)
        if entry is None:
            raise SemanticError(f"Error: '{lexeme}' was used but never declared.")
        return entry["address"]

    def get_type(self, lexeme):
        entry = self.lookup(lexeme)
        if entry is None:
            raise SemanticError(f"Error: '{lexeme}' was used but never declared.")
        return entry["type"]

    def print_table(self):
        lines = []
        lines.append("\n" + "=" * 45)
        lines.append("  Symbol Table")
        lines.append("=" * 45)
        lines.append(f"  {'Identifier':<15} {'MemoryLocation':<18} {'Type'}")
        lines.append("=" * 45)
        for lexeme, info in self._table.items():
            lines.append(f"  {lexeme:<15} {info['address']:<18} {info['type']}")
        lines.append("=" * 45 + "\n")
        return "\n".join(lines)


class InstructionTable:

    MAX_INSTRUCTIONS = 1000

    def __init__(self):
        self._table = []
        self._current_address = 1

    def generate(self, op, oprnd=None):
        if self._current_address > self.MAX_INSTRUCTIONS:
            raise RuntimeError("Too many instructions - exceeded limit of 1000.")
        entry = {
            "address": self._current_address,
            "op": op,
            "oprnd": oprnd,
        }
        self._table.append(entry)
        self._current_address += 1
        return self._current_address - 1

    def back_patch(self, instr_addr, oprnd_value):
        idx = instr_addr - 1
        if 0 <= idx < len(self._table):
            self._table[idx]["oprnd"] = oprnd_value

    @property
    def current_address(self):
        return self._current_address

    def print_table(self):
        lines = []
        lines.append("\n" + "=" * 40)
        lines.append("  Assembly Code Listing")
        lines.append("=" * 40)
        for entry in self._table:
            addr = entry["address"]
            op = entry["op"]
            oprnd = entry["oprnd"]
            if oprnd is None:
                lines.append(f"  {addr:<6}{op}")
            else:
                lines.append(f"  {addr:<6}{op:<12}{oprnd}")
        lines.append("=" * 40 + "\n")
        return "\n".join(lines)


class SemanticError(Exception):
    pass


class Parser:

    def __init__(self, tokens, print_switch=True):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if tokens else None
        self.print_switch = print_switch
        self.output = []
        self.sym_table = SymbolTable()
        self.instr_table = InstructionTable()
        self._jmp_stack = []
        self._current_decl_type = None

    def log_production(self, rule):
        if self.print_switch:
            rule = rule.replace("::=", "->").replace("<Empty>", "ε")
            self.output.append("    " + rule)

    def print_current_token(self):
        if self.current_token:
            t_type = self.current_token[0].capitalize()
            self.output.append(f"Token: {t_type:<16} Lexeme: {self.current_token[1]}")

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def match(self, token_type, token_value=None):
        if self.current_token and self.current_token[0] == token_type:
            if token_value is None or self.current_token[1] == token_value:
                self.advance()
                return True
        return False

    def peek_value(self):
        return self.current_token[1] if self.current_token else ""

    def peek_type(self):
        return self.current_token[0] if self.current_token else ""

    def error(self, message):
        if self.current_token:
            tok_type, lexeme, line = self.current_token
            raise Exception(f"Parser error at line {line}: Unexpected token '{lexeme}' of type {tok_type}. {message}")
        raise Exception(f"Parser error at end of file: {message}")

    def gen(self, op, oprnd=None):
        return self.instr_table.generate(op, oprnd)

    def back_patch(self, jmp_addr):
        addr = self._jmp_stack.pop()
        self.instr_table.back_patch(addr, jmp_addr)

    def push_jmp(self, addr):
        self._jmp_stack.append(addr)

    def parse(self, output_filename="output_assignment3.txt"):
        try:
            self.rat26s()
            result_lines = []
            result_lines.append("\nSyntax is correct.\n")
            result_lines.append(self.instr_table.print_table())
            result_lines.append(self.sym_table.print_table())
            full_output = "\n".join(self.output) + "\n" + "\n".join(result_lines)
            with open(output_filename, "w") as f:
                f.write(full_output)
            print(f"Parser output written to {output_filename}")
            return True, full_output
        except (Exception, SemanticError) as e:
            msg = str(e)
            with open(output_filename, "w") as f:
                f.write(msg + "\n")
            print(msg, file=sys.stderr)
            return False, msg

    def rat26s(self):
        if self.current_token and self.peek_value() == '@':
            self.print_current_token()
            self.log_production("<Rat26S> -> @ <Opt Function Definitions> @ <Opt Declaration List> @ <Statement List> @")
            self.match('separator', '@')
            self.opt_function_definitions()
            self.print_current_token()
            self.match('separator', '@')
            self.opt_declaration_list()
            self.print_current_token()
            self.match('separator', '@')
            self.statement_list()
            self.print_current_token()
            self.match('separator', '@')
        else:
            self.statement_list()

    def opt_function_definitions(self):
        if self.current_token and self.peek_value() == 'function':
            raise SemanticError("Error: Function definitions are not allowed in simplified Rat26S.")
        self.log_production("<Opt Function Definitions> -> ε")

    def opt_declaration_list(self):
        if self.peek_type() == 'keyword' and self.peek_value() in ('integer', 'boolean'):
            self.log_production("<Opt Declaration List> -> <Declaration List>")
            self.declaration_list()
        else:
            self.log_production("<Opt Declaration List> -> ε")

    def declaration_list(self):
        self.log_production("<Declaration List> -> <Declaration> ; <Declaration List'>")
        self.declaration()
        self.print_current_token()
        self.match('separator', ';')
        self.declaration_list_prime()

    def declaration_list_prime(self):
        if self.peek_type() == 'keyword' and self.peek_value() in ('integer', 'boolean'):
            self.log_production("<Declaration List'> -> <Declaration> ; <Declaration List'>")
            self.declaration()
            self.print_current_token()
            self.match('separator', ';')
            self.declaration_list_prime()
        else:
            self.log_production("<Declaration List'> -> ε")

    def declaration(self):
        self.log_production("<Declaration> -> <Qualifier> <IDs>")
        self.qualifier()
        self.ids(declaring=True)

    def qualifier(self):
        self.print_current_token()
        if self.peek_value() == 'integer':
            self._current_decl_type = 'integer'
            self.match('keyword', 'integer')
        elif self.peek_value() == 'boolean':
            self._current_decl_type = 'boolean'
            self.match('keyword', 'boolean')
        else:
            self.error("Expected qualifier (integer | boolean)")
        self.log_production("<Qualifier> -> integer | boolean")

    def ids(self, declaring=False):
        self.print_current_token()
        self.log_production("<IDs> -> <Identifier> <IDs'>")
        if self.peek_type() != 'identifier':
            self.error("Expected identifier")
        lexeme = self.current_token[1]
        self.advance()
        if declaring:
            self.sym_table.insert(lexeme, self._current_decl_type)
        else:
            self.sym_table.get_address(lexeme)
        self.ids_prime(declaring=declaring)

    def ids_prime(self, declaring=False):
        if self.peek_value() == ',':
            self.print_current_token()
            self.match('separator', ',')
            self.log_production("<IDs'> -> , <Identifier> <IDs'>")
            self.print_current_token()
            if self.peek_type() != 'identifier':
                self.error("Expected identifier after ','")
            lexeme = self.current_token[1]
            self.advance()
            if declaring:
                self.sym_table.insert(lexeme, self._current_decl_type)
            else:
                self.sym_table.get_address(lexeme)
            self.ids_prime(declaring=declaring)
        else:
            self.log_production("<IDs'> -> ε")

    def statement_list(self):
        self.log_production("<Statement List> -> <Statement> <Statement List'>")
        self.statement()
        self.statement_list_prime()

    def statement_list_prime(self):
        starters = ('{', 'if', 'while', 'write', 'read', 'return')
        if self.current_token and (self.peek_type() == 'identifier' or self.peek_value() in starters):
            self.log_production("<Statement List'> -> <Statement> <Statement List'>")
            self.statement()
            self.statement_list_prime()
        else:
            self.log_production("<Statement List'> -> ε")

    def statement(self):
        if self.current_token:
            if self.peek_value() == '{':
                self.log_production("<Statement> -> <Compound>")
                self.compound()
            elif self.peek_type() == 'identifier':
                self.log_production("<Statement> -> <Assign>")
                self.assign()
            elif self.peek_value() == 'if':
                self.log_production("<Statement> -> <If>")
                self._if()
            elif self.peek_value() == 'while':
                self.log_production("<Statement> -> <While>")
                self._while()
            elif self.peek_value() == 'write':
                self.log_production("<Statement> -> <Print>")
                self.print_statement()
            elif self.peek_value() == 'read':
                self.log_production("<Statement> -> <Scan>")
                self.scan()
            elif self.peek_value() == 'return':
                self.log_production("<Statement> -> <Return>")
                self._return()
            else:
                self.error("Invalid statement")

    def compound(self):
        self.print_current_token()
        self.log_production("<Compound> -> { <Statement List> }")
        self.match('separator', '{')
        self.statement_list()
        self.print_current_token()
        self.match('separator', '}')

    def assign(self):
        self.print_current_token()
        self.log_production("<Assign> -> <Identifier> = <Expression> ;")
        lexeme = self.current_token[1]
        addr = self.sym_table.get_address(lexeme)
        self.advance()
        self.print_current_token()
        if not self.match('operator', '='):
            self.error("Expected '='")
        self.expression()
        self.gen("POPM", addr)
        self.print_current_token()
        if not self.match('separator', ';'):
            self.error("Expected ';'")

    def _if(self):
        self.print_current_token()
        self.log_production("<If> -> if ( <Condition> ) <Statement> <If_Tail>")
        self.match('keyword', 'if')
        self.print_current_token()
        self.match('separator', '(')
        self.condition()
        self.print_current_token()
        self.match('separator', ')')
        self.statement()
        self.if_tail()

    def if_tail(self):
        if self.peek_value() == 'otherwise':
            self.print_current_token()
            self.match('keyword', 'otherwise')
            self.log_production("<If_Tail> -> otherwise <Statement> fi")
            jmp_addr = self.gen("JMP", None)
            self.back_patch(self.instr_table.current_address)
            self.push_jmp(jmp_addr)
            self.statement()
            self.back_patch(self.instr_table.current_address)
            self.print_current_token()
            if not self.match('keyword', 'fi'):
                self.error("Expected 'fi'")
        elif self.peek_value() == 'fi':
            self.log_production("<If_Tail> -> fi")
            self.gen("LABEL", None)
            self.back_patch(self.instr_table.current_address - 1)
            self.print_current_token()
            self.match('keyword', 'fi')
        else:
            self.error("Expected 'fi' or 'otherwise'")

    def _while(self):
        self.print_current_token()
        self.log_production("<While> -> while ( <Condition> ) <Statement>")
        self.match('keyword', 'while')
        label_addr = self.gen("LABEL", None)
        self.print_current_token()
        self.match('separator', '(')
        self.condition()
        self.print_current_token()
        self.match('separator', ')')
        self.statement()
        self.gen("JMP", label_addr)
        self.back_patch(self.instr_table.current_address)

    def _return(self):
        self.print_current_token()
        self.log_production("<Return> -> return <Return_Tail>")
        self.match('keyword', 'return')
        self.return_tail()

    def return_tail(self):
        if self.peek_value() == ';':
            self.print_current_token()
            self.match('separator', ';')
            self.log_production("<Return_Tail> -> ;")
        else:
            self.log_production("<Return_Tail> -> <Expression> ;")
            self.expression()
            self.print_current_token()
            self.match('separator', ';')

    def print_statement(self):
        self.print_current_token()
        self.log_production("<Print> -> write ( <Expression> );")
        self.match('keyword', 'write')
        self.print_current_token()
        self.match('separator', '(')
        self.expression()
        self.gen("SOUT", None)
        self.print_current_token()
        self.match('separator', ')')
        self.print_current_token()
        self.match('separator', ';')

    def scan(self):
        self.print_current_token()
        self.log_production("<Scan> -> read ( <IDs> );")
        self.match('keyword', 'read')
        self.print_current_token()
        self.match('separator', '(')
        self._scan_ids()
        self.print_current_token()
        self.match('separator', ')')
        self.print_current_token()
        self.match('separator', ';')

    def _scan_ids(self):
        self.print_current_token()
        if self.peek_type() != 'identifier':
            self.error("Expected identifier in read()")
        lexeme = self.current_token[1]
        addr = self.sym_table.get_address(lexeme)
        self.advance()
        self.gen("SIN", None)
        self.gen("POPM", addr)
        while self.peek_value() == ',':
            self.print_current_token()
            self.match('separator', ',')
            self.print_current_token()
            if self.peek_type() != 'identifier':
                self.error("Expected identifier after ','")
            lexeme = self.current_token[1]
            addr = self.sym_table.get_address(lexeme)
            self.advance()
            self.gen("SIN", None)
            self.gen("POPM", addr)

    def condition(self):
        self.log_production("<Condition> -> <Expression> <Relop> <Expression>")
        self.expression()
        op = self.relop()
        self.expression()
        relop_map = {
            '<':  "LES",
            '>':  "GRT",
            '==': "EQU",
            '!=': "NEQ",
            '<=': "LEQ",
            '=>': "GEQ",
        }
        instr = relop_map.get(op)
        if instr:
            self.gen(instr, None)
        jmpz_addr = self.gen("JMPZ", None)
        self.push_jmp(jmpz_addr)

    def relop(self):
        self.print_current_token()
        self.log_production("<Relop> -> == | != | > | < | <= | =>")
        valid = ('==', '!=', '>', '<', '<=', '=>')
        if self.current_token and self.current_token[0] == 'operator' and self.current_token[1] in valid:
            op = self.current_token[1]
            self.advance()
            return op
        self.error("Expected relational operator")

    def expression(self):
        self.log_production("<Expression> -> <Term> <Expression'>")
        self.term()
        self.expression_prime()

    def expression_prime(self):
        if self.peek_type() == 'operator' and self.peek_value() in ('+', '-'):
            self.print_current_token()
            op = self.current_token[1]
            self.advance()
            self.log_production(f"<Expression'> -> {op} <Term> <Expression'>")
            self.term()
            if op == '+':
                self.gen("A", None)
            else:
                self.gen("S", None)
            self.expression_prime()
        else:
            self.log_production("<Expression'> -> ε")

    def term(self):
        self.log_production("<Term> -> <Factor> <Term'>")
        self.factor()
        self.term_prime()

    def term_prime(self):
        if self.peek_type() == 'operator' and self.peek_value() in ('*', '/'):
            self.print_current_token()
            op = self.current_token[1]
            self.advance()
            self.log_production(f"<Term'> -> {op} <Factor> <Term'>")
            self.factor()
            if op == '*':
                self.gen("M", None)
            else:
                self.gen("D", None)
            self.term_prime()
        else:
            self.log_production("<Term'> -> ε")

    def factor(self):
        if self.peek_type() == 'operator' and self.peek_value() == '-':
            self.print_current_token()
            self.advance()
            self.log_production("<Factor> -> - <Primary>")
            self.primary()
        else:
            self.log_production("<Factor> -> <Primary>")
            self.primary()

    def primary(self):
        if self.peek_type() == 'identifier':
            self.print_current_token()
            lexeme = self.current_token[1]
            addr = self.sym_table.get_address(lexeme)
            self.advance()
            self.gen("PUSHM", addr)
            self.log_production("<Primary> -> <Identifier>")
        elif self.peek_type() == 'integer':
            self.print_current_token()
            val = int(self.current_token[1])
            self.advance()
            self.gen("PUSHI", val)
            self.log_production("<Primary> -> <Integer>")
        elif self.peek_value() in ('true', 'false'):
            self.print_current_token()
            val = 1 if self.current_token[1] == 'true' else 0
            self.advance()
            self.gen("PUSHI", val)
            self.log_production(f"<Primary> -> {'true' if val else 'false'}")
        elif self.peek_value() == '(':
            self.print_current_token()
            self.match('separator', '(')
            self.log_production("<Primary> -> ( <Expression> )")
            self.expression()
            self.print_current_token()
            if not self.match('separator', ')'):
                self.error("Expected ')' after expression")
        else:
            self.error("Invalid Primary")


def run_test_on_file(file_path):
    output_folder = "output_results"
    if os.path.exists("Assignment3") and os.path.isdir("Assignment3"):
        output_folder = os.path.join("Assignment3", "output_results")

    os.makedirs(output_folder, exist_ok=True)

    base_name = os.path.basename(file_path)
    output_filename = os.path.join(output_folder, os.path.splitext(base_name)[0] + ".out")

    print(f"\nRunning test on {file_path}...")
    try:
        with open(file_path, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        return

    from lexer import lexer
    tokens = lexer(source_code)

    parser = Parser(tokens)
    success, _ = parser.parse(output_filename)

    if success:
        print("Syntax is correct.")
        print(parser.instr_table.print_table())
        print(parser.sym_table.print_table())
        print(f"Output saved to: {output_filename}")
    else:
        print(f"Result: {base_name} - FAILED", file=sys.stderr)


if __name__ == '__main__':
    while True:
        print("\n" + "=" * 30)
        print("Rat26S Compiler - Assignment 3")
        print("=" * 30)
        print("1) Run Preset Test 1 (assignment3_sample.rat26)")
        print("2) Run Preset Test 2 (test2.rat26)")
        print("3) Run Preset Test 3 (test3.rat26)")
        print("C) Run Custom file")
        print("Q) Quit")

        choice = input("\nSelection: ").strip().lower()
        if choice == 'q':
            break

        filename = ""
        if choice == '1':
            filename = "assignment3_sample.rat26"
        elif choice == '2':
            filename = "test2.rat26"
        elif choice == '3':
            filename = "test3.rat26"
        elif choice == 'c':
            filename = input("Enter the filename to test: ").strip()
        else:
            print("Invalid selection.")
            continue

        if filename:
            if not os.path.exists(filename) and os.path.exists(os.path.join("Assignment3", filename)):
                filename = os.path.join("Assignment3", filename)
            run_test_on_file(filename)