"""
Assignment 3 - CS323: Symbol Table Handling & Assembly Code Generation
Simplified Rat26S: No function definitions, no real type.

Builds on Assignment 2 (Recursive Descent Parser).
New additions:
  - Symbol Table with memory addresses starting at 10000
  - Code generation using virtual stack-machine instructions
  - Back-patching for while and if jumps
"""

import sys
import os


# ─────────────────────────────────────────────────────────────
#  Symbol Table
# ─────────────────────────────────────────────────────────────

class SymbolTable:
    """
    Stores declared identifiers with their memory address and type.
    Memory addresses start at 10000 and increment by 1 per new identifier.
    """

    def __init__(self):
        self._table = {}           # {lexeme: {"address": int, "type": str}}
        self._memory_address = 10000

    # ── Insert ──────────────────────────────────────────────
    def insert(self, lexeme: str, var_type: str):
        """Insert a new identifier.  Raises SemanticError if already declared."""
        if lexeme in self._table:
            raise SemanticError(f"Identifier '{lexeme}' has already been declared.")
        self._table[lexeme] = {
            "address": self._memory_address,
            "type": var_type,
        }
        self._memory_address += 1

    # ── Lookup ───────────────────────────────────────────────
    def lookup(self, lexeme: str) -> dict:
        """Return the entry dict, or None if not found."""
        return self._table.get(lexeme)

    def get_address(self, lexeme: str) -> int:
        """Return memory address.  Raises SemanticError if undeclared."""
        entry = self.lookup(lexeme)
        if entry is None:
            raise SemanticError(f"Identifier '{lexeme}' used before declaration.")
        return entry["address"]

    def get_type(self, lexeme: str) -> str:
        entry = self.lookup(lexeme)
        if entry is None:
            raise SemanticError(f"Identifier '{lexeme}' used before declaration.")
        return entry["type"]

    # ── Print ────────────────────────────────────────────────
    def print_table(self) -> str:
        lines = []
        lines.append(f"\n{'─'*45}")
        lines.append(f"  SYMBOL TABLE")
        lines.append(f"{'─'*45}")
        lines.append(f"  {'Identifier':<15} {'MemoryLocation':<18} {'Type'}")
        lines.append(f"{'─'*45}")
        for lexeme, info in self._table.items():
            lines.append(f"  {lexeme:<15} {info['address']:<18} {info['type']}")
        lines.append(f"{'─'*45}\n")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
#  Instruction Table  (Code Generator)
# ─────────────────────────────────────────────────────────────

class InstructionTable:
    """
    Holds the generated assembly instructions.
    Instructions are 1-indexed (starts at 1).
    """

    MAX_INSTRUCTIONS = 1000

    def __init__(self):
        self._table = []          # list of {"address": int, "op": str, "oprnd": str|int|None}
        self._current_address = 1

    # ── Generate ─────────────────────────────────────────────
    def generate(self, op: str, oprnd=None):
        """Append one instruction and return its address."""
        if self._current_address > self.MAX_INSTRUCTIONS:
            raise RuntimeError("Instruction table overflow (>1000 instructions).")
        entry = {
            "address": self._current_address,
            "op": op,
            "oprnd": oprnd,
        }
        self._table.append(entry)
        self._current_address += 1
        return self._current_address - 1   # address of just-inserted instruction

    # ── Back-patch ───────────────────────────────────────────
    def back_patch(self, instr_addr: int, oprnd_value: int):
        """Fill in the operand of a previously emitted JMPZ/JMP instruction."""
        # Instructions are 1-indexed; list is 0-indexed
        idx = instr_addr - 1
        if 0 <= idx < len(self._table):
            self._table[idx]["oprnd"] = oprnd_value

    @property
    def current_address(self) -> int:
        return self._current_address

    # ── Print ────────────────────────────────────────────────
    def print_table(self) -> str:
        lines = []
        lines.append(f"\n{'─'*40}")
        lines.append(f"  ASSEMBLY CODE LISTING")
        lines.append(f"{'─'*40}")
        for entry in self._table:
            addr = entry["address"]
            op = entry["op"]
            oprnd = entry["oprnd"]
            if oprnd is None:
                lines.append(f"  {addr:<6}{op}")
            else:
                lines.append(f"  {addr:<6}{op:<12}{oprnd}")
        lines.append(f"{'─'*40}\n")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
#  Exceptions
# ─────────────────────────────────────────────────────────────

class SemanticError(Exception):
    pass


# ─────────────────────────────────────────────────────────────
#  Parser  (Assignment 3 — Simplified Rat26S)
# ─────────────────────────────────────────────────────────────

class Parser:
    """
    Recursive-descent parser for the *simplified* Rat26S language.
    Differences from Assignment 2:
      - No <Function Definitions> (always ε)
      - No 'real' type
      - Symbol table checking on every identifier use
      - Inline code generation
    """

    def __init__(self, tokens, print_switch=True):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if tokens else None
        self.print_switch = print_switch

        self.output = []              # parser trace lines
        self.sym_table = SymbolTable()
        self.instr_table = InstructionTable()
        self._jmp_stack = []          # stack of instr addresses for back-patching

        # Track the declared type currently being processed (for multi-id declarations)
        self._current_decl_type = None

    # ─────────────────────────────────────────────────────────
    #  Logging helpers
    # ─────────────────────────────────────────────────────────

    def _log(self, line: str):
        self.output.append(line)

    def log_token(self):
        if self.current_token:
            t_type = self.current_token[0].capitalize()
            self._log(f"  Token: {t_type:<16} Lexeme: {self.current_token[1]}")

    def log_production(self, rule: str):
        if self.print_switch:
            rule = rule.replace("::=", "->").replace("<Empty>", "ε")
            self._log(f"    {rule}")

    # ─────────────────────────────────────────────────────────
    #  Token helpers
    # ─────────────────────────────────────────────────────────

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def match(self, token_type: str, token_value=None) -> bool:
        if self.current_token and self.current_token[0] == token_type:
            if token_value is None or self.current_token[1] == token_value:
                self.advance()
                return True
        return False

    def peek_value(self) -> str:
        return self.current_token[1] if self.current_token else ""

    def peek_type(self) -> str:
        return self.current_token[0] if self.current_token else ""

    def error(self, message: str):
        if self.current_token:
            tok_type, lexeme, line = self.current_token
            raise Exception(f"Syntax error at line {line}: {message} (got '{lexeme}' / {tok_type})")
        raise Exception(f"Syntax error at end of file: {message}")

    # ─────────────────────────────────────────────────────────
    #  Code-generation helpers
    # ─────────────────────────────────────────────────────────

    def gen(self, op: str, oprnd=None) -> int:
        return self.instr_table.generate(op, oprnd)

    def back_patch(self, jmp_addr: int):
        """Pop from JMP stack and patch the operand to jmp_addr."""
        addr = self._jmp_stack.pop()
        self.instr_table.back_patch(addr, jmp_addr)

    def push_jmp(self, addr: int):
        self._jmp_stack.append(addr)

    # ─────────────────────────────────────────────────────────
    #  Top-level entry
    # ─────────────────────────────────────────────────────────

    def parse(self, output_filename="output_assignment3.txt"):
        try:
            self.rat26s()
            result_lines = []
            result_lines.append("\n✓ Syntax is correct.\n")
            result_lines.append(self.instr_table.print_table())
            result_lines.append(self.sym_table.print_table())
            full_output = "\n".join(self.output) + "\n" + "\n".join(result_lines)
            with open(output_filename, "w") as f:
                f.write(full_output)
            print(f"Done — output written to: {output_filename}")
            return True, full_output
        except (Exception, SemanticError) as e:
            msg = str(e)
            with open(output_filename, "w") as f:
                f.write(msg + "\n")
            print(f"ERROR: {msg}", file=sys.stderr)
            return False, msg

    # ─────────────────────────────────────────────────────────
    #  Grammar rules
    # ─────────────────────────────────────────────────────────

    # <Rat26S> -> @ <Opt Function Definitions> @ <Opt Declaration List> @ <Statement List> @
    def rat26s(self):
        if self.current_token and self.peek_value() == '@':
            self.log_token()
            self.log_production("<Rat26S> -> @ <Opt Function Definitions> @ <Opt Declaration List> @ <Statement List> @")
            self.match('separator', '@')
            self.opt_function_definitions()
            self.log_token()
            self.match('separator', '@')
            self.opt_declaration_list()
            self.log_token()
            self.match('separator', '@')
            self.statement_list()
            self.log_token()
            self.match('separator', '@')
        else:
            self.statement_list()

    # Simplified: no function definitions allowed
    def opt_function_definitions(self):
        if self.current_token and self.peek_value() == 'function':
            raise SemanticError("Simplified Rat26S does not allow function definitions.")
        self.log_production("<Opt Function Definitions> -> ε")

    # ── Declaration list ─────────────────────────────────────

    def opt_declaration_list(self):
        if self.peek_type() == 'keyword' and self.peek_value() in ('integer', 'boolean'):
            self.log_production("<Opt Declaration List> -> <Declaration List>")
            self.declaration_list()
        else:
            self.log_production("<Opt Declaration List> -> ε")

    def declaration_list(self):
        self.log_production("<Declaration List> -> <Declaration> ; <Declaration List'>")
        self.declaration()
        self.log_token()
        self.match('separator', ';')
        self.declaration_list_prime()

    def declaration_list_prime(self):
        if self.peek_type() == 'keyword' and self.peek_value() in ('integer', 'boolean'):
            self.log_production("<Declaration List'> -> <Declaration> ; <Declaration List'>")
            self.declaration()
            self.log_token()
            self.match('separator', ';')
            self.declaration_list_prime()
        else:
            self.log_production("<Declaration List'> -> ε")

    def declaration(self):
        self.log_production("<Declaration> -> <Qualifier> <IDs>")
        self.qualifier()          # sets self._current_decl_type
        self.ids(declaring=True)

    def qualifier(self):
        self.log_token()
        if self.peek_value() == 'integer':
            self._current_decl_type = 'integer'
            self.match('keyword', 'integer')
        elif self.peek_value() == 'boolean':
            self._current_decl_type = 'boolean'
            self.match('keyword', 'boolean')
        else:
            self.error("Expected qualifier (integer | boolean)")
        self.log_production("<Qualifier> -> integer | boolean")

    # ── IDs ──────────────────────────────────────────────────

    def ids(self, declaring=False):
        self.log_token()
        self.log_production("<IDs> -> <Identifier> <IDs'>")
        if self.peek_type() != 'identifier':
            self.error("Expected identifier")
        lexeme = self.current_token[1]
        self.advance()

        if declaring:
            # Insert into symbol table (raises SemanticError if duplicate)
            self.sym_table.insert(lexeme, self._current_decl_type)
        else:
            # Must already be declared
            self.sym_table.get_address(lexeme)   # raises if missing

        self.ids_prime(declaring=declaring)

    def ids_prime(self, declaring=False):
        if self.peek_value() == ',':
            self.log_token()
            self.match('separator', ',')
            self.log_production("<IDs'> -> , <Identifier> <IDs'>")
            self.log_token()
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

    # ── Statement list ───────────────────────────────────────

    def statement_list(self):
        self.log_production("<Statement List> -> <Statement> <Statement List'>")
        self.statement()
        self.statement_list_prime()

    def statement_list_prime(self):
        starters = ('{', 'if', 'while', 'write', 'read', 'return')
        if self.current_token and (
                self.peek_type() == 'identifier' or self.peek_value() in starters):
            self.log_production("<Statement List'> -> <Statement> <Statement List'>")
            self.statement()
            self.statement_list_prime()
        else:
            self.log_production("<Statement List'> -> ε")

    def statement(self):
        v = self.peek_value()
        if v == '{':
            self.log_production("<Statement> -> <Compound>")
            self.compound()
        elif self.peek_type() == 'identifier':
            self.log_production("<Statement> -> <Assign>")
            self.assign()
        elif v == 'if':
            self.log_production("<Statement> -> <If>")
            self._if()
        elif v == 'while':
            self.log_production("<Statement> -> <While>")
            self._while()
        elif v == 'write':
            self.log_production("<Statement> -> <Print>")
            self.print_statement()
        elif v == 'read':
            self.log_production("<Statement> -> <Scan>")
            self.scan()
        elif v == 'return':
            self.log_production("<Statement> -> <Return>")
            self._return()
        else:
            self.error("Expected a statement")

    # ── Compound ─────────────────────────────────────────────

    def compound(self):
        self.log_token()
        self.log_production("<Compound> -> { <Statement List> }")
        self.match('separator', '{')
        self.statement_list()
        self.log_token()
        self.match('separator', '}')

    # ── Assign  →  id = E ;    +   POPM ─────────────────────

    def assign(self):
        self.log_token()
        self.log_production("<Assign> -> <Identifier> = <Expression> ;")
        lexeme = self.current_token[1]
        addr = self.sym_table.get_address(lexeme)   # semantic check
        self.advance()
        self.log_token()
        if not self.match('operator', '='):
            self.error("Expected '='")
        self.expression()
        self.gen("POPM", addr)
        self.log_token()
        if not self.match('separator', ';'):
            self.error("Expected ';'")

    # ── If  →  if ( C ) S [otherwise S] fi ──────────────────

    def _if(self):
        self.log_token()
        self.log_production("<If> -> if ( <Condition> ) <Statement> <If_Tail>")
        self.match('keyword', 'if')
        self.log_token()
        self.match('separator', '(')
        self.condition()
        self.log_token()
        self.match('separator', ')')
        self.statement()
        self.if_tail()

    def if_tail(self):
        if self.peek_value() == 'otherwise':
            self.log_token()
            self.match('keyword', 'otherwise')
            self.log_production("<If_Tail> -> otherwise <Statement> fi")
            # Before the 'otherwise' body, emit JMP over it and back-patch JMPZ
            jmp_addr = self.gen("JMP", None)   # will be back-patched after fi
            self.back_patch(self.instr_table.current_address)  # patch the JMPZ from condition
            self.push_jmp(jmp_addr)            # push the new JMP for patching after fi
            self.statement()
            self.back_patch(self.instr_table.current_address)  # patch JMP
            self.log_token()
            if not self.match('keyword', 'fi'):
                self.error("Expected 'fi'")
        elif self.peek_value() == 'fi':
            self.log_production("<If_Tail> -> fi")
            # Back-patch the JMPZ from condition to here
            self.gen("LABEL", None)
            self.back_patch(self.instr_table.current_address - 1)
            self.log_token()
            self.match('keyword', 'fi')
        else:
            self.error("Expected 'fi' or 'otherwise'")

    # ── While  →  while ( C ) S  ─────────────────────────────

    def _while(self):
        self.log_token()
        self.log_production("<While> -> while ( <Condition> ) <Statement>")
        self.match('keyword', 'while')

        # Save address of LABEL as jump-back target
        label_addr = self.gen("LABEL", None)

        self.log_token()
        self.match('separator', '(')
        self.condition()       # emits comparison + JMPZ (with placeholder)
        self.log_token()
        self.match('separator', ')')
        self.statement()

        # Unconditional jump back to LABEL
        self.gen("JMP", label_addr)

        # Back-patch the JMPZ to the instruction after JMP
        self.back_patch(self.instr_table.current_address)

    # ── Return ───────────────────────────────────────────────

    def _return(self):
        self.log_token()
        self.log_production("<Return> -> return <Return_Tail>")
        self.match('keyword', 'return')
        self.return_tail()

    def return_tail(self):
        if self.peek_value() == ';':
            self.log_token()
            self.match('separator', ';')
            self.log_production("<Return_Tail> -> ;")
        else:
            self.log_production("<Return_Tail> -> <Expression> ;")
            self.expression()
            self.log_token()
            self.match('separator', ';')

    # ── Print  (write)  →  SOUT ──────────────────────────────

    def print_statement(self):
        self.log_token()
        self.log_production("<Print> -> write ( <Expression> );")
        self.match('keyword', 'write')
        self.log_token()
        self.match('separator', '(')
        self.expression()
        self.gen("SOUT", None)
        self.log_token()
        self.match('separator', ')')
        self.log_token()
        self.match('separator', ';')

    # ── Scan   (read)   →  SIN + POPM ───────────────────────

    def scan(self):
        self.log_token()
        self.log_production("<Scan> -> read ( <IDs> );")
        self.match('keyword', 'read')
        self.log_token()
        self.match('separator', '(')
        # Handle potentially multiple ids
        self._scan_ids()
        self.log_token()
        self.match('separator', ')')
        self.log_token()
        self.match('separator', ';')

    def _scan_ids(self):
        """read (a, b, c) → SIN+POPM for each."""
        self.log_token()
        if self.peek_type() != 'identifier':
            self.error("Expected identifier in read()")
        lexeme = self.current_token[1]
        addr = self.sym_table.get_address(lexeme)
        self.advance()
        self.gen("SIN", None)
        self.gen("POPM", addr)
        while self.peek_value() == ',':
            self.log_token()
            self.match('separator', ',')
            self.log_token()
            if self.peek_type() != 'identifier':
                self.error("Expected identifier after ','")
            lexeme = self.current_token[1]
            addr = self.sym_table.get_address(lexeme)
            self.advance()
            self.gen("SIN", None)
            self.gen("POPM", addr)

    # ── Condition  →  E R E  ─────────────────────────────────

    def condition(self):
        self.log_production("<Condition> -> <Expression> <Relop> <Expression>")
        self.expression()
        op = self.relop()       # returns the operator string
        self.expression()

        # Emit comparison instruction
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

        # Emit JMPZ with placeholder; push address for back-patching
        jmpz_addr = self.gen("JMPZ", None)
        self.push_jmp(jmpz_addr)

    def relop(self) -> str:
        self.log_token()
        self.log_production("<Relop> -> == | != | > | < | <= | =>")
        valid = ('==', '!=', '>', '<', '<=', '=>')
        if self.current_token and self.current_token[0] == 'operator' and self.current_token[1] in valid:
            op = self.current_token[1]
            self.advance()
            return op
        self.error("Expected relational operator")

    # ── Expression  →  T E'  ─────────────────────────────────

    def expression(self):
        self.log_production("<Expression> -> <Term> <Expression'>")
        self.term()
        self.expression_prime()

    def expression_prime(self):
        if self.peek_type() == 'operator' and self.peek_value() in ('+', '-'):
            self.log_token()
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

    # ── Term  →  F T'  ───────────────────────────────────────

    def term(self):
        self.log_production("<Term> -> <Factor> <Term'>")
        self.factor()
        self.term_prime()

    def term_prime(self):
        if self.peek_type() == 'operator' and self.peek_value() in ('*', '/'):
            self.log_token()
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

    # ── Factor  →  - Primary | Primary  ──────────────────────

    def factor(self):
        if self.peek_type() == 'operator' and self.peek_value() == '-':
            self.log_token()
            self.advance()
            self.log_production("<Factor> -> - <Primary>")
            self.primary()
        else:
            self.log_production("<Factor> -> <Primary>")
            self.primary()

    # ── Primary  ─────────────────────────────────────────────

    def primary(self):
        if self.peek_type() == 'identifier':
            self.log_token()
            lexeme = self.current_token[1]
            addr = self.sym_table.get_address(lexeme)
            self.advance()
            self.gen("PUSHM", addr)
            self.log_production("<Primary> -> <Identifier>")

        elif self.peek_type() == 'integer':
            self.log_token()
            val = int(self.current_token[1])
            self.advance()
            self.gen("PUSHI", val)
            self.log_production("<Primary> -> <Integer>")

        elif self.peek_value() in ('true', 'false'):
            self.log_token()
            val = 1 if self.current_token[1] == 'true' else 0
            self.advance()
            self.gen("PUSHI", val)
            self.log_production(f"<Primary> -> {'true' if val else 'false'}")

        elif self.peek_value() == '(':
            self.log_token()
            self.match('separator', '(')
            self.log_production("<Primary> -> ( <Expression> )")
            self.expression()
            self.log_token()
            if not self.match('separator', ')'):
                self.error("Expected ')' after expression")
        else:
            self.error("Invalid primary expression")


# ─────────────────────────────────────────────────────────────
#  Run helper
# ─────────────────────────────────────────────────────────────

def run_on_file(file_path: str, output_path: str = None, print_switch=True):
    """Lex, parse, and generate code for a Rat26S source file."""
    try:
        with open(file_path, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.", file=sys.stderr)
        return

    from lexer import lexer
    tokens = lexer(source)

    if output_path is None:
        base = os.path.splitext(os.path.basename(file_path))[0]
        out_dir = os.path.dirname(file_path) or "."
        output_path = os.path.join(out_dir, base + "_output.txt")

    parser = Parser(tokens, print_switch=print_switch)
    success, full_text = parser.parse(output_path)

    if success:
        # Also pretty-print to console
        print(parser.instr_table.print_table())
        print(parser.sym_table.print_table())
    return success


# ─────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Locate test files (support running from repo root or Assignment3 dir)
    def find_file(name):
        candidates = [
            name,
            os.path.join("Assignment3", name),
            os.path.join("..", "Assignment2", name),
            os.path.join("Assignment2", name),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    while True:
        print("\n" + "=" * 40)
        print("  CS323 Assignment 3 — Rat26S Compiler")
        print("  (Symbol Table + Code Generator)")
        print("=" * 40)
        print("  1) Test: assignment3_sample.rat26")
        print("  2) Test: test2.rat26 (if/otherwise)")
        print("  3) Test: test3.rat26 (while loop)")
        print("  C) Custom file")
        print("  Q) Quit")

        choice = input("\nSelection: ").strip().lower()
        if choice == 'q':
            break

        filename = None
        if choice == '1':
            filename = find_file("assignment3_sample.rat26")
        elif choice == '2':
            filename = find_file("test2.rat26")
        elif choice == '3':
            filename = find_file("test3.rat26")
        elif choice == 'c':
            filename = input("Enter filename: ").strip()
        else:
            print("Invalid choice.")
            continue

        if filename and os.path.exists(filename):
            run_on_file(filename)
        else:
            print(f"File not found: {filename}")
