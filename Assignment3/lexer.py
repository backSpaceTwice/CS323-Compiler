import os

# Language Definition for Rat26S (simplified - no function definitions, no real type)
KEYWORDS = {
    "integer", "boolean",
    "if", "otherwise", "fi",
    "while", "return",
    "read", "write",
    "true", "false"
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
        if char.isalpha():  input_type = 'letter'
        elif char.isdigit(): input_type = 'digit'
        elif char == '_':    input_type = '_'
        if input_type is None:
            return 'reject'
        state = self.transition_table.get((self.current_state, input_type))
        return state if state else 'reject'


class IntegerFSM:
    def __init__(self):
        self.current_state = '1'
        self.accepting_states = {'2'}
        self.transition_table = {('1', 'digit'): '2', ('2', 'digit'): '2'}

    def next_state(self, char):
        input_type = 'digit' if char.isdigit() else None
        if input_type is None:
            return 'reject'
        state = self.transition_table.get((self.current_state, input_type))
        return state if state else 'reject'


def lexer(content):
    content += " "
    char_pointer = 0
    length = len(content)
    tokens_and_lexemes = []
    line = 1

    while char_pointer < length:
        if content[char_pointer].isspace():
            if content[char_pointer] == "\n":
                line += 1
            char_pointer += 1
            continue

        if content[char_pointer] == "/" and char_pointer + 1 < length and content[char_pointer + 1] == "*":
            char_pointer += 2
            while char_pointer + 1 < length:
                if content[char_pointer] == "\n":
                    line += 1
                if content[char_pointer] == "*" and content[char_pointer + 1] == "/":
                    char_pointer += 2
                    break
                char_pointer += 1
            continue

        token_start_line = line

        if char_pointer + 1 < length:
            two_char = content[char_pointer: char_pointer + 2]
            if two_char in OPERATORS:
                tokens_and_lexemes.append(("operator", two_char, token_start_line))
                char_pointer += 2
                continue

        one_char = content[char_pointer]
        if one_char in SEPARATORS:
            tokens_and_lexemes.append(("separator", one_char, token_start_line))
            char_pointer += 1
            continue
        if one_char in OPERATORS:
            tokens_and_lexemes.append(("operator", one_char, token_start_line))
            char_pointer += 1
            continue

        id_fsm = IdentifierFSM()
        int_fsm = IntegerFSM()

        last_valid_type = None
        last_valid_lexeme = ""

        current_id_lexeme = ""
        current_int_lexeme = ""

        temp_ptr = char_pointer
        while temp_ptr < length:
            c = content[temp_ptr]
            any_active = False

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
                else:
                    id_fsm.current_state = 'reject'

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
                else:
                    int_fsm.current_state = 'reject'

            if not any_active:
                break
            temp_ptr += 1

        if last_valid_type:
            tokens_and_lexemes.append((last_valid_type, last_valid_lexeme, token_start_line))
            char_pointer += len(last_valid_lexeme)
        else:
            if char_pointer < length - 1:
                tokens_and_lexemes.append(("invalid", content[char_pointer], token_start_line))
            char_pointer += 1

    return tokens_and_lexemes
