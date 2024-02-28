from Parser.transition_diagram_parser import TransitionDiagramParser
from scanner.scanner import Scanner
from Parser.parser import Parser
from Parser.grammar import Grammar
import subprocess


# Mahdi Saadatbakht     99105475
# Mohammad Mowlavi      99105753


class Compiler:
    def __init__(self, input_file):
        self.input_file = input_file

    def compile(self):
        parser = Parser(Scanner(self.input_file), Grammar())
        # parser = TransitionDiagramParser(Scanner(self.input_file), Grammar())
        parser.parse()

    def print_output(self):
        wsl_command = "wsl /mnt/d/university/6th_term/cd/project/tester_linux.out"
        output = subprocess.check_output(wsl_command, shell=True, text=True)
        lines = output.split('\n')
        output = ''
        for line in lines:
            if line.startswith('PRINT'):
                output += line + '\n'

        with open('expected.txt', mode='w') as f:
            f.write(output)


def main():
    compiler = Compiler('input.txt')
    compiler.compile()
    compiler.print_output()


if __name__ == '__main__':
    main()
