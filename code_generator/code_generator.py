class AddressManager:
    DEFAULT_WORD_SIZE = 4
    DEFAULT_INDEX_INCREMENT = 1

    def __init__(self):
        self.__index = 0
        self.__temp_address = 500
        self.__code_gen_symbol_table = []

    def get_temp_address(self):
        return self.__temp_address

    def get_index(self):
        return self.__index

    def increase_temp_address(self, amount=None):
        if amount is None:
            amount = AddressManager.DEFAULT_WORD_SIZE
        self.__temp_address += amount

    def increase_index(self, amount=None):
        if amount is None:
            amount = AddressManager.DEFAULT_INDEX_INCREMENT
        self.__index += amount

    def is_in_symbol_table(self, item, scope_num=0):
        for i in self.__code_gen_symbol_table[::-1]:
            if item == i[0] and i[3] <= scope_num:
                return True
        return False

    def find_symbol_address(self, symbol):
        if symbol == 'output':
            return symbol
        # if symbol == 'arr':
        #     print('symbol_table', self.__code_gen_symbol_table)
        for i in self.__code_gen_symbol_table[::-1]:
            if symbol == i[0]:
                return i[2]

    def extend_symbol_table(self, symbol_info):
        self.__code_gen_symbol_table.append(symbol_info)

    def get_last_id_in_symbol_table(self):
        return self.__code_gen_symbol_table[-1]

    def delete_last_id_in_symbol_table(self):
        del self.__code_gen_symbol_table[-1]

    def get_ids_from_symbol_table(self):
        return self.__code_gen_symbol_table


class Executor:
    DEBUG_MODE = False

    def __init__(self, address_manager):
        self.__program_block = {}
        self.__semantic_errors = []
        self.__address_manager = address_manager

    def get_program_block(self):
        return self.__program_block

    def add_three_address_code(self, operator, op1, op2=None, op3=None, index=None, debug=None, increase_index=False):
        if index is None:
            index = self.__address_manager.get_index()
        code = f"({operator}, {op1}, {'' if op2 is None else op2}, {'' if op3 is None else op3})"
        if debug is not None and Executor.DEBUG_MODE:
            code += ' ' + debug
        self.__program_block[index] = code
        if increase_index:
            self.__address_manager.increase_index()

    def get_elements_from_semantic_stack(self, number=1, pop=True):
        pass

    def scope_check(self, token_line, token_name, scope):
        if self.__address_manager.is_in_symbol_table(token_name, scope) or token_name == 'output':
            return
        self.__semantic_errors.append(f'#{token_line}: Semantic Error! \'{token_name}\' is not defined.')

    def void_check(self, variable_id, current_id, current_id_line):
        if current_id == 'void':
            self.__semantic_errors.append(
                f'#{current_id_line}: Semantic Error! Illegal type of void for \'{variable_id}\'.')

    def break_check(self, token_line, repeats):
        if len(repeats) > 0:
            return
        self.__semantic_errors.append(
            f'#{token_line}: Semantic Error! No \'repeat ... until\' found for \'break\'.')

    def type_mismatch(self, token_line, operand_1, operand_2, in_multiplication):
        if operand_2 is None or operand_1 is None:
            return
        symbol_table_ids = self.__address_manager.get_ids_from_symbol_table()

        def get_operand_type(operand):
            if operand.startswith('#'):
                return 'int'
            for s in symbol_table_ids:
                if s[2] == operand:
                    return s[1]
            print(operand)
            return 'int'

        operand_1_type = get_operand_type(operand_1)
        operand_2_type = get_operand_type(operand_2)

        if operand_2_type == operand_1_type:
            return
        operand_1_type = 'array' if operand_1_type == 'int*' else operand_1_type
        operand_2_type = 'array' if operand_2_type == 'int*' else operand_2_type
        if in_multiplication:
            self.__semantic_errors.append(
                f'#{token_line}: Semantic Error! Type mismatch in operands, Got array instead of int.')
        else:
            self.__semantic_errors.append(
                f'#{token_line}: Semantic Error! Type mismatch in operands, Got {operand_2_type} instead of {operand_1_type}.')

    def parameter_num_matching(self, token_line, args, attributes):
        function_name = None
        symbol_table_ids = self.__address_manager.get_ids_from_symbol_table()
        for i in symbol_table_ids:
            if i[2] == attributes:
                function_name = i[0]
        function_arguments = []
        for i in attributes:
            if isinstance(i, list):
                function_arguments = i
        if len(function_arguments) != len(args):
            self.__semantic_errors.append(
                f'#{token_line}: Semantic Error! Mismatch in numbers of arguments of \'{function_name}\'.')

    def parameter_type_matching(self, token_line, var, arg, num, function_name):
        def get_type_string(type_name):
            return 'array' if type_name == 'int*' else type_name

        arg_type = 'int' if arg.startswith('#') else next(
            (rec[1] for rec in self.__address_manager.get_ids_from_symbol_table() if rec[2] == arg), None)
        if arg_type and arg_type != var[1]:
            expected_type = get_type_string(var[1])
            actual_type = get_type_string(arg_type)
            self.__semantic_errors.append(
                f'#{token_line}: Semantic Error! Mismatch in type of argument {num} of \'{function_name}\'. Expected \'{expected_type}\' but got \'{actual_type}\' instead.')

    def get_semantic_errors(self):
        return self.__semantic_errors


class CodeGen:
    def __init__(self):
        self.address_manager = AddressManager()
        self.executor = Executor(self.address_manager)
        self.semantic_stack = []
        self.new_Symbol_table = {}
        self.break_stack = []
        self.current_scope = 0
        self.return_stack = []
        self.id_type = None
        self.in_repeat = []
        self.in_multiplication = False
        self.in_params = False
        self.call_sequence = []
        self.methods = {
            '#get_id_type': self.get_id_type,
            '#push_id': self.push_id,
            '#define_variable': self.define_variable,
            '#push_num': self.push_num,
            '#define_array': self.define_array,
            '#start_params': self.start_params,
            '#start_function': self.start_function,
            '#return_from_func': self.return_from_func,
            '#define_array_argument': self.define_array_argument,
            '#push_scope': self.push_scope,
            '#pop_scope': self.pop_scope,
            '#clean_up': self.clean_up,
            '#break_loop': self.break_loop,
            '#save': self.save,
            '#jpf_save': self.jpf_save,
            '#jump': self.jump,
            '#start_repeat': self.start_repeat,
            '#end_repeat': self.end_repeat,
            '#save_return': self.save_return,
            '#push_index': self.push_index,
            '#get_id': self.get_id,
            '#assign_operation': self.assign_operation,
            '#push_operator': self.push_operator,
            '#make_op': self.make_op,
            '#multiply': self.multiply,
            '#call_func': self.call_func,
            '#array_index': self.array_index,
        }

    def call(self, action_symbol, token_line, token_name):
        self.call_sequence.append((action_symbol, token_line, token_name))
        self.methods[action_symbol](token_line, token_name)
        # self.export('')

    def export(self, path):
        with open('output1.txt', "a") as f:
            f.write(f'{self.__dict__}\n')
            f.write('==================================\n')

    def get_temp(self, count=1, initialize=True, debug=None):
        begin_address = str(self.address_manager.get_temp_address())
        for _ in range(count):
            self.address_manager.increase_temp_address()
        return begin_address

    def define_variable(self, token_name, token_line):
        variable_id = self.semantic_stack.pop()
        self.executor.void_check(variable_id, self.id_type[1], self.id_type[0])
        variable_address = self.get_temp(initialize=False, debug='define_variable')
        if self.in_params:
            scope = self.current_scope + 1
        else:
            scope = self.current_scope
        self.address_manager.extend_symbol_table((variable_id, 'int', variable_address, scope))

    def define_array(self, token_name, token_line):
        array_size, array_id = int(self.semantic_stack.pop()[1:]), self.semantic_stack.pop()

        self.executor.void_check(array_id, self.id_type[1], self.id_type[0])
        address = self.get_temp(initialize=False, debug='void_check')
        array_space = self.get_temp(array_size, debug='void_check_arr_space')
        self.executor.add_three_address_code(
            operator='ASSIGN', op1=f'#{array_space}', op2=address, op3=None, index=None,
            debug='define_array', increase_index=True)
        self.address_manager.extend_symbol_table((array_id, 'int*', address, self.current_scope))

    def get_id_type(self, token_line, token_name):
        self.id_type = (token_line, token_name)

    def push_id(self, token_line, token_name):
        self.semantic_stack.append(token_name)
        self.new_Symbol_table[(token_name, self.current_scope)] = self.id_type[1]

    def get_id(self, token_line, token_name):
        self.executor.scope_check(token_line, token_name, self.current_scope)
        # print('get_id', token_name, self.address_manager.find_symbol_address(token_name))
        # print('get_id', token_name, self.current_scope, self.semantic_stack)
        self.semantic_stack.append(self.address_manager.find_symbol_address(token_name))

    def push_num(self, token_line, token_name):
        self.semantic_stack.append(f'#{token_name}')

    def push_operator(self, token_line, token_name):
        self.semantic_stack.append(token_name)

    def get_equivalent_operator(self, operator):
        if operator == '+':
            return 'ADD'
        elif operator == '-':
            return 'SUB'
        elif operator == '<':
            return 'LT'
        elif operator == '==':
            return 'EQ'
        raise Exception(f"in get_equivalent_operator operator == {operator}, How this is possible?")

    def make_op(self, token_line, token_name):
        op2, operator, op1 = self.semantic_stack.pop(), self.semantic_stack.pop(), self.semantic_stack.pop()
        self.executor.type_mismatch(token_line, op1, op2, self.in_multiplication)
        address = self.get_temp(initialize=False, debug='make_op')
        self.executor.add_three_address_code(
            operator=self.get_equivalent_operator(operator), op1=op1, op2=op2, op3=address, index=None,
            debug='make_op', increase_index=True)
        self.semantic_stack.append(address)

    def assign_operation(self, token_name, token_line):
        self.executor.add_three_address_code(
            operator='ASSIGN', op1=self.semantic_stack[-1], op2=self.semantic_stack[-2], op3=None, index=None,
            debug='assign_operation', increase_index=True)
        self.semantic_stack.pop()

    def multiply(self, token_line, token_name):
        res = self.get_temp(initialize=False, debug='multiply')
        self.in_multiplication = True
        self.executor.type_mismatch(token_line, self.semantic_stack[-2], self.semantic_stack[-1],
                                    self.in_multiplication)
        self.in_multiplication = False
        self.executor.add_three_address_code(
            operator='MULT', op1=self.semantic_stack[-1], op2=self.semantic_stack[-2], op3=res, index=None,
            debug='multiply',
            increase_index=True
        )
        self.semantic_stack.pop(), self.semantic_stack.pop(), self.semantic_stack.append(res)

    def define_array_argument(self, token_name, token_line):
        temp = self.address_manager.get_last_id_in_symbol_table()
        self.address_manager.delete_last_id_in_symbol_table()
        self.address_manager.extend_symbol_table((temp[0], 'int*', temp[2], temp[3]))

    def array_index(self, token_line, token_name):
        idx, array_address = self.semantic_stack.pop(), self.semantic_stack.pop()
        temp, result = self.get_temp(initialize=False, debug='array_index'), self.get_temp(initialize=False,
                                                                                           debug='array_index')
        self.executor.add_three_address_code(
            operator='MULT', op1='#4', op2=idx, op3=temp, index=None,
            debug='array_index', increase_index=True)
        self.executor.add_three_address_code(
            operator='ASSIGN', op1=array_address, op2=result, op3=None, index=None,
            debug='array_index', increase_index=True)
        self.executor.add_three_address_code(
            operator='ADD', op1=result, op2=temp, op3=result, index=None,
            debug='array_index', increase_index=True)
        self.semantic_stack.append(f'@{result}')

    def save(self, token_name, token_line):
        self.semantic_stack.append(self.address_manager.get_index())
        self.address_manager.increase_index()

    def start_repeat(self, token_name, token_line):
        self.semantic_stack.append(self.address_manager.get_index())
        self.in_repeat.append(1)
        self.break_stack.append('begin')

    def end_repeat(self, token_name, token_line):
        self.semantic_stack.append(self.address_manager.get_index())
        self.address_manager.increase_index()

        self.executor.add_three_address_code(
            operator='JPF', op1=self.semantic_stack[-2], op2=self.semantic_stack[-3], op3=None,
            index=int(self.semantic_stack[-1]), debug='end_repeat'
        )
        self.executor.add_three_address_code(
            operator='JP', op1=self.address_manager.get_index() + 1, op2=None, op3=None, index=None, debug='end_repeat'
        )
        self.address_manager.increase_index()
        self.semantic_stack.pop(), self.semantic_stack.pop(), self.semantic_stack.pop()

        latest_block = len(self.break_stack) - self.break_stack[::-1].index('begin') - 1
        for index in self.break_stack[latest_block + 1:]:
            self.executor.add_three_address_code(
                operator='JP', op1=self.address_manager.get_index(), op2=None, op3=None, index=index, debug='end_repeat'
            )
        self.break_stack = self.break_stack[:latest_block]
        self.in_repeat.pop()

    def jpf_save(self, token_name, token_line):
        destination_address = self.semantic_stack.pop()
        source_address = self.semantic_stack.pop()
        self.executor.add_three_address_code(
            operator='JPF', op1=source_address, op2=self.address_manager.get_index() + 1, op3=None,
            index=destination_address, debug='jpf_save'
        )
        self.semantic_stack.append(self.address_manager.get_index())
        self.address_manager.increase_index()

    def jump(self, token_name, token_line):
        dest = int(self.semantic_stack.pop())
        self.executor.add_three_address_code(
            operator='JP', op1=self.address_manager.get_index(), op2=None, op3=None, index=dest, debug='jump'
        )

    def break_loop(self, token_line, token_name):
        self.executor.break_check(token_line, self.in_repeat)
        self.break_stack.append(self.address_manager.get_index())
        self.address_manager.increase_index()

    def clean_up(self, token_name, token_line):
        self.semantic_stack.pop()

    def call_func(self, token_line, token_name):
        if self.semantic_stack[-2] == 'output':
            self.executor.add_three_address_code(
                operator='PRINT', op1=self.semantic_stack.pop(), op2=None, op3=None, index=None,
                debug='call_func', increase_index=True)
        if self.semantic_stack[-1] == 'output':
            return
        arguments, attrs = [], []
        for i in self.semantic_stack[::-1]:
            if isinstance(i, list):
                attrs = i
                break
            arguments = [i] + arguments
        self.executor.parameter_num_matching(token_line, arguments, attrs)
        # print('call_func', arguments, attrs, self.semantic_stack)
        for var, arg in zip(attrs[1], arguments):
            self.executor.parameter_type_matching(token_line, var, arg, attrs[1].index(var) + 1,
                                                  self.get_func_name(var))
            self.executor.add_three_address_code(
                operator='ASSIGN', op1=arg, op2=var[2], op3=None, index=None, debug='call_func0',
                increase_index=True
            )
            self.semantic_stack.pop()
        for i in range(len(arguments) - len(attrs[1]) + 1):
            self.semantic_stack.pop()
        self.executor.add_three_address_code(
            operator='ASSIGN', op1=f'#{self.address_manager.get_index() + 3}', op2=attrs[2], op3=None,
            index=None, debug='call_func1', increase_index=True
        )
        self.executor.add_three_address_code(
            operator='ASSIGN', op1='#0', op2=attrs[0], op3=None,
            index=None, debug='call_func2', increase_index=True,
        )
        self.executor.add_three_address_code(
            operator='JP', op1=attrs[-1], op2=None, op3=None,
            index=None, debug='call_func', increase_index=True,
        )
        # print(token_name, symbol_table_ids)
        # for item in symbol_table_ids[::-1]:
        #     if item[0] == token_name:
        #         print(item)
        result_address = self.get_temp(initialize=False, debug='call_func')
        self.executor.add_three_address_code(
            operator='ASSIGN', op1=attrs[0], op2=result_address, op3=None,
            index=None, debug='call_func2', increase_index=True
        )
        self.semantic_stack.append(result_address)

    def start_params(self, token_name, token_line):
        self.in_params = True
        function_name = self.semantic_stack.pop()
        self.semantic_stack.append(self.address_manager.get_index())
        self.address_manager.increase_index()
        self.semantic_stack.append(function_name)
        self.address_manager.extend_symbol_table('start')

    def push_index(self, token_name, token_line):
        self.semantic_stack.append(f'#{self.address_manager.get_index()}')

    def save_return(self, token_name, token_line):
        self.return_stack.append((self.address_manager.get_index(), self.semantic_stack[-1]))
        self.semantic_stack.pop()
        # print('save_return', self.address_manager.get_ids_from_symbol_table())
        self.address_manager.increase_index(2)

    def start_function(self, token_name, token_line):
        self.in_params = False
        return_address, return_value = self.get_temp(initialize=False, debug='start_function'), self.get_temp(
            initialize=False, debug='start_function')
        pb_index = self.address_manager.get_index()
        self.semantic_stack.append(return_value)
        self.semantic_stack.append(return_address)
        function_name = self.semantic_stack[-3]
        symbol_table_ids = self.address_manager.get_ids_from_symbol_table()
        args_start_idx = symbol_table_ids.index('start')
        func_args = symbol_table_ids[args_start_idx + 1:]
        symbol_table_ids.pop(args_start_idx)
        symbol_table_ids.append(
            (function_name, 'function', [return_value, func_args, return_address, pb_index], self.current_scope,
             self.id_type[1]))
        # print('start_function', symbol_table_ids)
        self.return_stack.append('begin')

    def return_from_func(self, token_name, token_line):
        last_function = len(self.return_stack) - self.return_stack[::-1].index('begin') - 1
        return_value, return_address = self.semantic_stack[-2], self.semantic_stack[-1]
        for address_info in self.return_stack[last_function + 1:]:
            self.executor.add_three_address_code(
                operator='ASSIGN', op1=address_info[1], op2=return_value, op3=None, index=address_info[0],
                debug='return_from_func0'
            )
            self.executor.add_three_address_code(
                operator='JP', op1='@' + str(return_address), op2=None, op3=None, index=address_info[0] + 1,
                debug='return_from_func0'
            )
        self.return_stack = self.return_stack[:last_function]

        if self.semantic_stack[-3] != 'main':
            return_address = self.semantic_stack[-1]
            self.executor.add_three_address_code(
                operator='JP', op1='@' + str(return_address), op2=None, op3=None, index=None,
                debug='return_from_func1', increase_index=True)

        self.semantic_stack.pop(), self.semantic_stack.pop(), self.semantic_stack.pop()
        symbol_table_ids = self.address_manager.get_ids_from_symbol_table()
        for symbol_info in symbol_table_ids[::-1]:
            if symbol_info[1] == 'function' and symbol_info[0] == 'main':
                index = self.semantic_stack.pop()
                temp = self.get_temp(initialize=False, debug='return_from_func1')
                self.executor.add_three_address_code(
                    operator='ASSIGN', op1='#0', op2=temp, op3=None, index=index, debug='return_from_func1'
                )
                return
            break
        index = self.semantic_stack.pop()
        self.executor.add_three_address_code(
            operator='JP', op1=self.address_manager.get_index(), op2=None, op3=None, index=index,
            debug='return_from_func2',
        )

    def get_func_name(self, var):
        for rec in self.address_manager.get_ids_from_symbol_table():
            if rec[1] == 'function':
                for arg in rec[2][1]:
                    if arg[2] == var[2]:
                        return rec[0]

    def push_scope(self, token_name, token_line):
        self.current_scope += 1

    def pop_scope(self, token_name, token_line):
        symbol_table_ids = self.address_manager.get_ids_from_symbol_table()
        for record in symbol_table_ids[::-1]:
            if record[3] == self.current_scope:
                symbol_table_ids.remove(record)
        # print('pop_scope', symbol_table_ids)
        self.current_scope -= 1
