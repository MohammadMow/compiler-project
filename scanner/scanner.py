from utils.buffer import Buffer
from utils.tables import *
from scanner.default_dfa import get_default_dfa
from scanner.dfa_handler import DFANode, ErrorNode, NonTokenizableNode
from scanner.enums_constants import get_keywords, TokenType


class Scanner:
    def __init__(self, input_file_name):
        self.buffer = Buffer(input_file_name)
        self.tokens = [[]]
        self.symbols = get_keywords()
        self.errors = []
        self.tokens_table, self.symbols_table, self.errors_table = None, None, None

    def get_current_line(self):
        return self.buffer.current_line

    def get_defaults(self):
        return get_default_dfa(), self.get_current_line(), ''

    def get_next_token(self):
        curr_state, tmp_curr_line, lexeme = self.get_defaults()
        eof = False

        while True:
            next_char = self.buffer.get_next_char()

            if not next_char:
                eof = True
            else:
                lexeme += next_char
                curr_state = curr_state.accept(lexeme)

            if isinstance(curr_state, NonTokenizableNode) and (curr_state.finished or eof):
                if eof and lexeme.startswith('/*'):
                    self.handle_error(ErrorNode(curr_state, lexeme), tmp_curr_line)
                curr_state, tmp_curr_line, lexeme = self.get_defaults()
            elif isinstance(curr_state, DFANode) and (curr_state.finished or eof):
                if curr_state.roll_back:
                    self.buffer.rollback(lexeme[-1])
                    lexeme = lexeme[:-1]
                curr_state.set_lexeme(lexeme)
                if eof:
                    return TokenType.EOF.value, '$'
                return curr_state.get_token(lexeme)
            elif isinstance(curr_state, ErrorNode):
                self.handle_error(curr_state, tmp_curr_line)
                curr_state, tmp_curr_line, lexeme = self.get_defaults()

            if eof:
                return TokenType.EOF.value, '$'

    def handle_error(self, error_state, current_line):
        error = list(error_state.handle_error())
        if error_state.dfa_node.roll_back:
            self.buffer.rollback(error_state.lexeme[-1])
            error[0] = error[0][:-1]
        self.errors.append((current_line, error[0], error[1]))

    def tokenize(self):
        while True:
            tmp_current_line = self.get_current_line()
            token = self.get_next_token()
            if token[0] == 'EOF':
                break
            while self.get_current_line() > tmp_current_line:
                self.tokens.append([])
                tmp_current_line += 1
            self.tokens[-1].append(token)

            token_type, token_value = token
            if token_type == TokenType.Id.value and token_value not in self.symbols:
                self.symbols.append(token_value)

        self.__create_tables()
        self.__export_tables()

    def __create_tables(self):
        self.tokens_table = TokensTable(self.tokens)
        self.symbols_table = SymbolsTable(self.symbols)
        self.errors_table = ErrorsTable(self.errors)

    def __export_tables(self):
        self.tokens_table.export()
        self.symbols_table.export()
        self.errors_table.export_lexical_errors()
