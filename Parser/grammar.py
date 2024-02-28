import json

from anytree import Node


class Terminal(Node):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.name = name

    def __str__(self):
        return self.name


class NonTerminal(Node):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.name = name
        self.first = []
        self.follow = []

    def __str__(self):
        return self.name


class Action(Node):
    def __init__(self, name, **kwargs):
        super(Action, self).__init__(name, **kwargs)
        self.name = name

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self.name)


class ProductRule:
    def __init__(self, lhs: NonTerminal, rhs: list):
        self.lhs = lhs
        self.rhs = rhs
        self.predict_set = []

    def __str__(self):
        return str(self.lhs)
        # return f'{str(self.lhs)} -> {" ".join([str(term) for term in self.rhs])}'


class Grammar:
    def __init__(self):
        self.terminals = []
        self.non_terminals = []
        self.product_rules = []
        self.rule_counter = 1
        self.import_terminals()
        self.import_non_terminals()
        self.import_firsts()
        self.import_follows()
        self.import_product_rules()
        self.import_predicts()

    def add_product_rule(self, rule):
        self.product_rules.append(rule)

    def get_term_by_name(self, name):
        for non_terminal in self.non_terminals:
            if non_terminal.name == name:
                return non_terminal
        for terminal in self.terminals:
            if terminal.name == name:
                return terminal
        return Action(name)

    def get_rules_by_lhs(self, name):
        rules = []
        for rule in self.product_rules:
            if rule.lhs.name == name:
                rules.append(rule)
        return rules

    def import_terminals(self):
        with open('Parser/data.json', encoding='utf-8') as f:
            terminals = json.load(f)['terminals']
            self.terminals = [Terminal(term) for term in terminals]

    def import_non_terminals(self):
        with open('Parser/data.json', encoding='utf-8') as f:
            non_terminals = json.load(f)['non-terminals']
            self.non_terminals = [NonTerminal(term) for term in non_terminals]

    def import_firsts(self):
        with open('Parser/data.json', encoding='utf-8') as f:
            first = json.load(f)['first']
            for key, value in first.items():
                non_terminal = self.get_term_by_name(key)
                non_terminal.first = [self.get_term_by_name(term) for term in value]

    def import_follows(self):
        with open('Parser/data.json', encoding='utf-8') as f:
            follow = json.load(f)['follow']
            for key, value in follow.items():
                non_terminal = self.get_term_by_name(key)
                non_terminal.follow = [self.get_term_by_name(term) for term in value]

    def import_product_rules(self):
        with open('Parser/code_gen_grammar.txt', encoding='utf-8') as f:
            for line in f.readlines():
                lhs_as_str, rhs_as_str = line.strip('\n').split(' -> ')
                lhs = self.get_term_by_name(lhs_as_str)
                for rule in rhs_as_str.split('|'):
                    terms = [self.get_term_by_name(term) for term in rule.split()]
                    self.add_product_rule(ProductRule(lhs, terms))

    def import_predicts(self):
        with open('Parser/predict.txt', encoding='utf-8') as f:
            for i, line in enumerate(f.readlines()):
                rule = self.product_rules[i]
                rule.predict_set = line.strip('\n').split(' ')
