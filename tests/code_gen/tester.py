from tests.tester import test

OUTPUT_FILES = {'expected.txt': 0, 'semantic_errors.txt': 0}


if __name__ == '__main__':
    test(output_files=OUTPUT_FILES, tests_path='testcases', num_tests=20)
