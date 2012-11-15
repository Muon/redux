from redux.types import str_
from redux.visitor import ASTTransformer

class StringInliner(ASTTransformer):
    """Inlines all string references."""
    def __init__(self):
        super(ASTTransformer, self).__init__()
        self.scopes = []

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def find_variable(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise KeyError(name)

    def visit_BitfieldAssignment(self, bitfield_assignment):
        return bitfield_assignment

    def visit_VarRef(self, var_ref):
        try:
            var = self.find_variable(var_ref.name)
            if var.type is str_:
                return var
            else:
                return var_ref
        except KeyError:
            return var_ref

    def visit_Assignment(self, assignment):
        assignment.expression = self.visit(assignment.expression)
        try:
            self.find_variable(assignment.variable.name)
        except KeyError:
            self.scopes[-1][assignment.variable.name] = assignment.expression

        if assignment.expression.type is str_:
            return None
        else:
            return assignment
