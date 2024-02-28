from tests.tester import test

OUTPUT_FILES = {'parse_tree.txt': 0, 'syntax_errors.txt': 0}


if __name__ == '__main__':
    test(output_files=OUTPUT_FILES, tests_path='testcases', num_tests=11)
