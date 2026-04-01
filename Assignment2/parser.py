import sys
import os

class Parser:
    """
    A recursive descent parser for the Rat26S language.
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        self.output = []

    def log_production(self, rule):
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

    def error(self, message):
        if self.current_token:
            token_type, lexeme, line_number = self.current_token
            error_message = f"Parser error at line {line_number}: Unexpected token '{lexeme}' of type {token_type}. {message}"
        else:
            error_message = f"Parser error at end of file: {message}"
        raise Exception(error_message)

    def parse(self, output_filename="parser_output.txt"):
        try:
            self.rat26s()
            print("Syntax is correct.")
            with open(output_filename, "w") as f:
                for line in self.output:
                    f.write(line + "\n")
            print(f"Parser output written to {output_filename}")
            return True
        except Exception as e:
            print(e, file=sys.stderr)
            with open(output_filename, "w") as f:
                f.write(str(e))
            return False

    def rat26s(self):
        if self.current_token and self.current_token[1] == '@':
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
        if self.current_token and self.current_token[1] == 'function':
            self.log_production("<Opt Function Definitions> -> <Function Definitions>")
            self.function_definitions()
        else:
            self.log_production("<Opt Function Definitions> -> ε")

    def function_definitions(self):
        self.log_production("<Function Definitions> -> <Function> <Function Definitions'>")
        self.function()
        self.function_definitions_prime()

    def function_definitions_prime(self):
        if self.current_token and self.current_token[1] == 'function':
            self.log_production("<Function Definitions'> -> <Function> <Function Definitions'>")
            self.function()
            self.function_definitions_prime()
        else:
            self.log_production("<Function Definitions'> -> ε")

    def function(self):
        self.print_current_token()
        self.log_production("<Function> -> function <Identifier> ( <Opt Parameter List> ) <Opt Declaration List> <Body>")
        self.match('keyword', 'function')
        self.print_current_token()
        self.match('identifier')
        self.print_current_token()
        self.match('separator', '(')
        self.opt_parameter_list()
        self.print_current_token()
        self.match('separator', ')')
        self.opt_declaration_list()
        self.body()

    def opt_parameter_list(self):
        if self.current_token and self.current_token[0] == 'identifier':
            self.log_production("<Opt Parameter List> -> <Parameter List>")
            self.parameter_list()
        else:
            self.log_production("<Opt Parameter List> -> ε")

    def parameter_list(self):
        self.log_production("<Parameter List> -> <Parameter> <Parameter List'>")
        self.parameter()
        self.parameter_list_prime()

    def parameter_list_prime(self):
        if self.current_token and self.current_token[1] == ',':
            self.print_current_token()
            self.match('separator', ',')
            self.log_production("<Parameter List'> -> , <Parameter> <Parameter List'>")
            self.parameter()
            self.parameter_list_prime()
        else:
            self.log_production("<Parameter List'> -> ε")

    def parameter(self):
        self.log_production("<Parameter> -> <IDs> <Qualifier>")
        self.ids()
        self.qualifier()

    def qualifier(self):
        self.print_current_token()
        self.log_production("<Qualifier> -> integer | boolean | real")
        if not (self.match('keyword', 'integer') or self.match('keyword', 'boolean') or self.match('keyword', 'real')):
            self.error("Expected qualifier")

    def body(self):
        self.print_current_token()
        self.log_production("<Body> -> { <Statement List> }")
        self.match('separator', '{')
        self.statement_list()
        self.print_current_token()
        self.match('separator', '}')

    def opt_declaration_list(self):
        if self.current_token and self.current_token[0] == 'keyword' and self.current_token[1] in ['integer', 'boolean', 'real']:
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
        if self.current_token and self.current_token[0] == 'keyword' and self.current_token[1] in ['integer', 'boolean', 'real']:
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
        self.ids()

    def ids(self):
        self.print_current_token()
        self.log_production("<IDs> -> <Identifier> <IDs'>")
        self.match('identifier')
        self.ids_prime()

    def ids_prime(self):
        if self.current_token and self.current_token[1] == ',':
            self.print_current_token()
            self.match('separator', ',')
            self.log_production("<IDs'> -> , <Identifier> <IDs'>")
            self.print_current_token()
            self.match('identifier')
            self.ids_prime()
        else:
            self.log_production("<IDs'> -> ε")

    def statement_list(self):
        self.log_production("<Statement List> -> <Statement> <Statement List'>")
        self.statement()
        self.statement_list_prime()

    def statement_list_prime(self):
        if self.current_token and (self.current_token[1] == '{' or self.current_token[0] == 'identifier' or self.current_token[1] in ['if', 'return', 'write', 'read', 'while']):
            self.log_production("<Statement List'> -> <Statement> <Statement List'>")
            self.statement()
            self.statement_list_prime()
        else:
            self.log_production("<Statement List'> -> ε")

    def statement(self):
        if self.current_token:
            if self.current_token[1] == '{':
                self.log_production("<Statement> -> <Compound>")
                self.compound()
            elif self.current_token[0] == 'identifier':
                self.log_production("<Statement> -> <Assign>")
                self.assign()
            elif self.current_token[1] == 'if':
                self.log_production("<Statement> -> <If>")
                self._if()
            elif self.current_token[1] == 'return':
                self.log_production("<Statement> -> <Return>")
                self._return()
            elif self.current_token[1] == 'write':
                self.log_production("<Statement> -> <Print>")
                self.print_statement()
            elif self.current_token[1] == 'read':
                self.log_production("<Statement> -> <Scan>")
                self.scan()
            elif self.current_token[1] == 'while':
                self.log_production("<Statement> -> <While>")
                self._while()
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
        self.match('identifier')
        self.print_current_token()
        self.match('operator', '=')
        self.expression()
        self.print_current_token()
        self.match('separator', ';')

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
        if self.current_token and self.current_token[1] == 'otherwise':
            self.print_current_token()
            self.match('keyword', 'otherwise')
            self.log_production("<If_Tail> -> otherwise <Statement> fi")
            self.statement()
            self.print_current_token()
            self.match('keyword', 'fi')
        elif self.current_token and self.current_token[1] == 'fi':
            self.print_current_token()
            self.match('keyword', 'fi')
            self.log_production("<If_Tail> -> fi")

    def _return(self):
        self.print_current_token()
        self.log_production("<Return> -> return <Return_Tail>")
        self.match('keyword', 'return')
        self.return_tail()

    def return_tail(self):
        if self.current_token and self.current_token[1] == ';':
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
        self.ids()
        self.print_current_token()
        self.match('separator', ')')
        self.print_current_token()
        self.match('separator', ';')

    def _while(self):
        self.print_current_token()
        self.log_production("<While> -> while ( <Condition> ) <Statement>")
        self.match('keyword', 'while')
        self.print_current_token()
        self.match('separator', '(')
        self.condition()
        self.print_current_token()
        self.match('separator', ')')
        self.statement()

    def condition(self):
        self.log_production("<Condition> -> <Expression> <Relop> <Expression>")
        self.expression()
        self.relop()
        self.expression()

    def relop(self):
        self.print_current_token()
        self.log_production("<Relop> -> == | != | > | < | <= | =>")
        if not (self.match('operator', '==') or self.match('operator', '!=') or self.match('operator', '>') or self.match('operator', '<') or self.match('operator', '<=') or self.match('operator', '=>')):
            self.error("Expected Relop")

    def expression(self):
        self.log_production("<Expression> -> <Term> <Expression'>")
        self.term()
        self.expression_prime()

    def expression_prime(self):
        if self.current_token and self.current_token[0] == 'operator' and self.current_token[1] in ['+', '-']:
            self.print_current_token()
            op = self.current_token[1]
            self.match('operator', op)
            self.log_production(f"<Expression'> -> {op} <Term> <Expression'>")
            self.term()
            self.expression_prime()
        else:
            self.log_production("<Expression'> -> ε")

    def term(self):
        self.log_production("<Term> -> <Factor> <Term'>")
        self.factor()
        self.term_prime()

    def term_prime(self):
        if self.current_token and self.current_token[0] == 'operator' and self.current_token[1] in ['*', '/']:
            self.print_current_token()
            op = self.current_token[1]
            self.match('operator', op)
            self.log_production(f"<Term'> -> {op} <Factor> <Term'>")
            self.factor()
            self.term_prime()
        else:
            self.log_production("<Term'> -> ε")

    def factor(self):
        if self.current_token and self.current_token[0] == 'operator' and self.current_token[1] == '-':
            self.print_current_token()
            self.match('operator', '-')
            self.log_production("<Factor> -> - <Primary>")
            self.primary()
        else:
            self.log_production("<Factor> -> <Primary>")
            self.primary()

    def primary(self):
        if self.current_token and self.current_token[0] == 'identifier':
            self.print_current_token()
            self.log_production("<Primary> -> <Identifier> <Primary_Tail>")
            self.match('identifier')
            self.primary_tail()
        elif self.current_token and self.current_token[0] == 'integer':
            self.print_current_token()
            self.log_production("<Primary> -> <Integer>")
            self.match('integer')
        elif self.current_token and self.current_token[0] == 'real':
            self.print_current_token()
            self.log_production("<Primary> -> <Real>")
            self.match('real')
        elif self.current_token and self.current_token[1] in ('true', 'false'):
            self.print_current_token()
            val = self.current_token[1]
            self.log_production(f"<Primary> -> {val}")
            self.match('keyword', val)
        elif self.current_token and self.current_token[1] == '(':
            self.print_current_token()
            self.log_production("<Primary> -> ( <Expression> )")
            self.match('separator', '(')
            self.expression()
            self.print_current_token()
            if not self.match('separator', ')'):
                self.error("Expected ')' after expression")
        else:
            self.error("Invalid Primary")

    def primary_tail(self):
        if self.current_token and self.current_token[1] == '(':
            self.print_current_token()
            self.match('separator', '(')
            self.log_production("<Primary_Tail> -> ( <IDs> )")
            self.ids()
            self.print_current_token()
            if not self.match('separator', ')'):
                self.error("Expected ')' after IDs in function call")
        else:
            self.log_production("<Primary_Tail> -> ε")

def run_test_on_file(file_path):
    """
    Runs the parser on a single file.
    """
    output_folder = "output_results"
    # If running from project root, use Assignment2/output_results
    if os.path.exists("Assignment2") and os.path.isdir("Assignment2"):
        output_folder = os.path.join("Assignment2", "output_results")
    
    os.makedirs(output_folder, exist_ok=True)
    
    base_name = os.path.basename(file_path)
    output_filename = os.path.join(output_folder, os.path.splitext(base_name)[0] + ".out")
    
    print(f"\nRunning test on {file_path}...")
    try:
        with open(file_path, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        # Try to help the user find the file
        search_dir = "Assignment2" if os.path.exists("Assignment2") else "."
        files = [f for f in os.listdir(search_dir) if f.endswith('.rat26') or f.endswith('.txt')]
        if files:
            print(f"Available files in {search_dir}:", ", ".join(files))
        return

    from lexer import lexer
    tokens = lexer(source_code)

    parser = Parser(tokens)
    success = parser.parse(output_filename)

    if success:
        print(f"Result: {base_name} - Syntax is correct.")
        print(f"Output saved to: {output_filename}")
    else:
        print(f"Result: {base_name} - FAILED", file=sys.stderr)

if __name__ == '__main__':
    while True:
        print("\n" + "="*30)
        print("Rat26S Syntax Analyzer")
        print("="*30)
        print("1) Run Preset Test 1 (test1.rat26)")
        print("2) Run Preset Test 2 (test2.rat26)")
        print("3) Run Preset Test 3 (test3.rat26)")
        print("C) Run Custom file")
        print("Q) Quit")

        choice = input("\nSelection: ").strip().lower()
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
            print("Invalid selection.")
            continue

        if filename:
            # Check if file exists, or try with Assignment2 prefix if not found
            if not os.path.exists(filename) and os.path.exists(os.path.join("Assignment2", filename)):
                filename = os.path.join("Assignment2", filename)
            
            run_test_on_file(filename)

