import os
import subprocess
import shutil

ROOT_DIR = '../../'
OUTPUT_FILES = None
TESTS_PATH = None


class Color:
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def compare_files(file1_path, file2_path):
    with open(file1_path, 'r') as f1, open(file2_path, 'r') as f2:
        lines1, lines2 = f1.readlines(), f2.readlines()
        lines1 = [line.strip() for line in lines1 if line.strip() != '']
        lines2 = [line.strip() for line in lines2 if line.strip() != '']
        if len(lines1) != len(lines2):
            return False
        for i in range(len(lines1)):
            if lines1[i] != lines2[i]:
                return False
    return True


def get_number_of_tests():
    return len(next(os.walk(f'{TESTS_PATH}/'))[1])


def is_output_correct(i):
    print(f'---------- T{i:02} ------------')
    result = True
    for file in OUTPUT_FILES.keys():
        dst = f'{TESTS_PATH}/T{i:02}/{file}'
        if not os.path.exists(ROOT_DIR + file):
            is_identical = False
            string_to_print = f'{Color.RED}FAILED{Color.END}'
        else:
            is_identical = compare_files(ROOT_DIR + file, dst)
            if is_identical:
                OUTPUT_FILES[file] += 1
                string_to_print = f'{Color.GREEN}PASSED{Color.END}'
            else:
                string_to_print = f'{Color.RED}FAILED{Color.END}'
        print(f'{file.split(".")[0]}: {string_to_print}')
        result = is_identical and result

    return result


def remove_output_files():
    for file in OUTPUT_FILES.keys():
        os.remove(ROOT_DIR + file)


def test(output_files, tests_path, num_tests=10):
    global OUTPUT_FILES, TESTS_PATH
    OUTPUT_FILES = output_files
    TESTS_PATH = tests_path

    num_passed_tests = 0
    for i in range(1, num_tests + 1):
        src = f'{tests_path}/T{i:02}/input.txt'
        dst = ROOT_DIR + 'input.txt'
        shutil.copyfile(src, dst)
        subprocess.run(['python', 'compiler.py'], cwd=ROOT_DIR)
        if is_output_correct(i):
            string_to_print = f'{Color.GREEN}{Color.BOLD}PASSED!{Color.END}'
            num_passed_tests += 1
        else:
            string_to_print = f'{Color.RED}{Color.BOLD}FAILED!{Color.END}'
        print(f'******* T{i:02} {string_to_print} *******\n')

    for file, num_passed in OUTPUT_FILES.items():
        print(f'{file.split(".")[0]}: {num_passed} / {num_tests}')
    print(f'{Color.BOLD}TOTAL: {num_passed_tests} / {num_tests}{Color.END}')
