from codegenerator import compile_script
from argparse import ArgumentParser
from os.path import splitext

parser = ArgumentParser(description='Compile a Redux script to Rescript.')
parser.add_argument('filenames', metavar='FILE', nargs='+',
                    help='script to be compiled to Rescript')

args = parser.parse_args()

for filename in args.filenames:
    with open(filename, "rt") as file_:
        input_code = file_.read()

    base_filename, extension = splitext(filename)
    with open(base_filename + ".ais", "wt") as file_:
        file_.write(compile_script(input_code))
