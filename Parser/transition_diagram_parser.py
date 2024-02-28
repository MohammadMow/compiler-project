from anytree import PreOrderIter, RenderTree

from Parser.grammar import NonTerminal, Terminal, Action
from code_generator.code_generator import CodeGen
from scanner.enums_constants import TokenType, get_symbols, get_keywords
from utils.tables import ROOT_DIR, ErrorsTable


class TransitionDiagramParser:
    def __init__(self, scanner, grammar):
        self.scanner = scanner
        self.grammar = grammar
        self.root = NonTerminal('Program')
        self.current_token = None
        self.errors = []
        self.unexpected_eof_reached = False
        self.code_gen = CodeGen()

    def get_next_token(self):
        token = self.scanner.get_next_token()
        return token

    def parse(self):
        self.current_token = self.get_next_token()

        self.procedure(self.root)
        if not self.unexpected_eof_reached:
            self.match(TokenType.EOF.value, self.root)

        self.export_semantic_errors()
        self.export_program_block()

        self.export_parse_tree()
        self.export_syntax_errors()

    def procedure(self, non_terminal: NonTerminal):
        for rule in self.grammar.get_rules_by_lhs(non_terminal.name):
            if self.current_token[0] in rule.predict_set or \
                    self.current_token[1] in rule.predict_set:
                self.call_rule(non_terminal, rule.rhs)
                break
        else:
            if self.current_token[1] in [term.name for term in non_terminal.follow]:
                if 'EPSILON' not in [term.name for term in non_terminal.first]:
                    self.errors.append(
                        (self.scanner.get_current_line(), '', f'syntax error, missing {non_terminal.name}'))
                non_terminal.parent = None
            else:
                if self.eof_reached():
                    self.errors.append((self.scanner.get_current_line(), '', 'syntax error, Unexpected EOF'))
                    self.unexpected_eof_reached = True
                    non_terminal.parent = None
                else:
                    if self.current_token[0] in ['NUM', 'ID']:
                        illegal_lookahead = self.current_token[0]
                    else:
                        illegal_lookahead = self.current_token[1]
                    self.errors.append((self.scanner.get_current_line(), '', f'syntax error, illegal {illegal_lookahead}'))
                    self.current_token = self.get_next_token()
                    self.procedure(non_terminal)

    def call_rule(self, parent, rhs: list):
        for term in rhs:
            if self.unexpected_eof_reached:
                return
            elif isinstance(term, NonTerminal):
                nt = NonTerminal(term.name, parent=parent)
                nt.first = term.first
                nt.follow = term.follow
                self.procedure(nt)
            elif isinstance(term, Terminal):
                self.match(term.name, parent)
            # elif isinstance(term, Action):
            #     self.code_gen.call(term.name, self.scanner.get_current_line(), self.current_token[1])

    def match(self, expected_token: str, parent):
        if expected_token in ['NUM', 'ID']:
            if self.current_token[0] == expected_token:
                Terminal(f'({self.current_token[0]}, {self.current_token[1]})', parent=parent)
                self.current_token = self.get_next_token()
                return

        if expected_token in get_keywords() or expected_token in get_symbols() or expected_token == '==':
            if self.current_token[1] == expected_token:
                Terminal(f'({self.current_token[0]}, {self.current_token[1]})', parent=parent)
                self.current_token = self.get_next_token()
                return

        if expected_token == 'EPSILON':
            Terminal('EPSILON', parent=parent)
        elif expected_token == TokenType.EOF.value:
            Terminal('$', parent=parent)
        else:
            self.errors.append((self.scanner.get_current_line(), '', f'syntax error, missing {expected_token}'))

    def eof_reached(self):
        return self.current_token[0] == TokenType.EOF.value

    def export_parse_tree(self):
        for node in PreOrderIter(self.root):
            if node.name == 'EPSILON':
                node.name = 'epsilon'
            elif type(node.name) is tuple:
                node.name = f'({node.name[0]}, {node.name[1]})'
        with open(ROOT_DIR + 'parse_tree.txt', 'w', encoding='utf-8') as f:
            string = ''
            for pre, _, node in RenderTree(self.root):
                string += f'{pre}{node.name}\n'
            f.write(string[:-1])

    def export_syntax_errors(self):
        errors_table = ErrorsTable(self.errors)
        errors_table.export_syntax_errors()

    def export_semantic_errors(self):
        with open('semantic_errors.txt', 'w') as f:
            if self.code_gen.executor.get_semantic_errors():
                for i in range(len(self.code_gen.executor.get_semantic_errors())):
                    f.write(f'{self.code_gen.executor.get_semantic_errors()[i]}\n')
            else:
                f.write("The input program is semantically correct.\n")

    def export_program_block(self):
        with open('output.txt', 'w') as f:
            if self.code_gen.executor.get_semantic_errors():
                f.write("The output code has not been generated.")
            else:
                program_block = self.code_gen.executor.get_program_block()
                for i in sorted(program_block.keys()):
                    f.write(f'{i}\t{program_block[i]}\n')
