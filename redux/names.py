from redux.typeannotate import INITIAL_SCOPE
from redux.intrinsics import get_intrinsic_functions

def get_initial_names():
    for name in INITIAL_SCOPE:
        yield name
    for name, _ in get_intrinsic_functions():
        yield name
