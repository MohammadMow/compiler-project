from scanner.dfa_handler import DFANode, RegexEdge, NonTokenizableNode
from scanner.enums_constants import TokenType


def build_dfa_of_num(start_dfa_node):
    # states
    digit_dfa = DFANode(token_type=TokenType.Num.value)
    finish_digit_dfa = DFANode(finished=True, roll_back=True, token_type=TokenType.Num.value)

    # transitions
    digit_start_edge = RegexEdge().accept_digits()
    digit_middle_edge = RegexEdge().accept_digits()
    digit_final_edge = RegexEdge().accept_white_spaces().accept_symbols().accept_comments()

    # create dfa
    start_dfa_node.add_next_node(edge=digit_start_edge, next_node=digit_dfa)
    digit_dfa.add_next_node(edge=digit_middle_edge, next_node=digit_dfa)
    digit_dfa.add_next_node(edge=digit_final_edge, next_node=finish_digit_dfa)


def build_rename_of_id_keyword(start_dfa_node):
    # states
    id_keyword_start_dfa = DFANode(token_type=TokenType.KeywordId.value)
    id_keyword_middle_dfa = DFANode(token_type=TokenType.KeywordId.value)
    id_keyword_finish_dfa = DFANode(finished=True, roll_back=True, token_type=TokenType.KeywordId.value)

    # transitions
    id_keyword_start_edge = RegexEdge().accept_alphabets()
    id_keyword_middle_edge = RegexEdge().accept_digits().accept_alphabets()
    id_keyword_final_edge = RegexEdge().accept_symbols().accept_comments().accept_white_spaces()

    # create dfa
    start_dfa_node.add_next_node(edge=id_keyword_start_edge, next_node=id_keyword_start_dfa)
    id_keyword_start_dfa.add_next_node(edge=id_keyword_middle_edge, next_node=id_keyword_middle_dfa)
    id_keyword_start_dfa.add_next_node(edge=id_keyword_final_edge, next_node=id_keyword_finish_dfa)
    id_keyword_middle_dfa.add_next_node(edge=id_keyword_middle_edge, next_node=id_keyword_middle_dfa)
    id_keyword_middle_dfa.add_next_node(edge=id_keyword_final_edge, next_node=id_keyword_finish_dfa)


def build_rename_of_symbol(start_dfa_node):
    # states
    symbols_group = DFANode(finished=True, token_type=TokenType.Symbol.value)
    symbol_equals = DFANode(token_type=TokenType.Symbol.value)
    symbol_assign = DFANode(token_type=TokenType.Symbol.value)
    symbol_star = DFANode(token_type=TokenType.Symbol.value)
    symbol_assign_star_finisher = DFANode(finished=True, roll_back=True, token_type=TokenType.Symbol.value)

    # transitions
    symbols_except_equal_star = RegexEdge().accept_symbols().reject('=').reject('*')
    symbol_equal_edge = RegexEdge().accept('=')
    symbol_star_edge = RegexEdge().accept('*')
    everything_except_slash = RegexEdge().accept_digits().accept_white_spaces().accept_comments().accept_alphabets().accept_symbols().reject('/')
    everything = RegexEdge().accept_digits().accept_white_spaces().accept_comments().accept_alphabets().accept_symbols()

    # create dfa
    start_dfa_node.add_next_node(edge=symbols_except_equal_star, next_node=symbols_group)
    symbol_equals.add_next_node(edge=everything, next_node=symbol_assign_star_finisher)
    start_dfa_node.add_next_node(edge=symbol_equal_edge, next_node=symbol_assign)
    start_dfa_node.add_next_node(edge=symbol_star_edge, next_node=symbol_star)
    symbol_assign.add_next_node(edge=symbol_equal_edge, next_node=symbol_equals)
    symbol_assign.add_next_node(edge=everything, next_node=symbol_assign_star_finisher)
    symbol_star.add_next_node(edge=everything_except_slash, next_node=symbol_assign_star_finisher)


def build_rename_of_whitespace(start_dfa_node):
    # states
    white_space_dfa = NonTokenizableNode(finished=True, token_type=TokenType.Whitespace.value)

    # transitions
    white_space_start_edge = RegexEdge().accept_white_spaces()

    # create dfa
    start_dfa_node.add_next_node(edge=white_space_start_edge, next_node=white_space_dfa)


def build_rename_of_comment(start_dfa_node):
    # states
    comment_start = NonTokenizableNode(token_type=TokenType.Comment.value)
    comment_middle = NonTokenizableNode(token_type=TokenType.Comment.value)
    comment_pre_final = NonTokenizableNode(token_type=TokenType.Comment.value)
    comment_final = NonTokenizableNode(finished=True, token_type=TokenType.Comment.value)

    # transitions
    symbol_slash = RegexEdge().accept('/')
    symbol_star = RegexEdge().accept('*')
    everything_except_star = RegexEdge().reject('*')
    everything_except_star_slash = RegexEdge().reject('*').reject('/')

    # create dfa
    start_dfa_node.add_next_node(edge=symbol_slash, next_node=comment_start)
    comment_start.add_next_node(edge=symbol_star, next_node=comment_middle)
    comment_middle.add_next_node(edge=everything_except_star, next_node=comment_middle)
    comment_middle.add_next_node(edge=symbol_star, next_node=comment_pre_final)
    comment_pre_final.add_next_node(edge=symbol_star, next_node=comment_pre_final)
    comment_pre_final.add_next_node(edge=symbol_slash, next_node=comment_final)
    comment_pre_final.add_next_node(edge=everything_except_star_slash, next_node=comment_middle)


def get_default_dfa():
    start_dfa_node = DFANode(token_type=TokenType.Unknown.value)

    build_dfa_of_num(start_dfa_node)
    build_rename_of_id_keyword(start_dfa_node)
    build_rename_of_symbol(start_dfa_node)
    build_rename_of_whitespace(start_dfa_node)
    build_rename_of_comment(start_dfa_node)

    return start_dfa_node
