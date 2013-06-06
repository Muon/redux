from redux.codegenerator import compile_script
from argparse import ArgumentParser
from os.path import splitext

parser = ArgumentParser(description='Compile a Redux script to Rescript.')
parser.add_argument('input_filename', metavar='FILE',
                    help='script to be compiled to Rescript')
parser.add_argument('output_filename', metavar='FILE',
                    help='script to be compiled to Rescript')

args = parser.parse_args()

filename = args.input_filename
assert filename, "no input file given"

with open(filename, "rt") as file_:
    input_code = file_.read()

output_code = compile_script(filename, input_code)

base_filename, extension = splitext(filename)
with open(args.output_filename, "wt") as file_:
    file_.write(output_code)
