from redux.visitor import ASTTransformer
from redux.names import get_initial_names

class AssignmentScopeAnalyzer(ASTTransformer):
    def __init__(self):
        super(AssignmentScopeAnalyzer, self).__init__()
        self.names = [set(get_initial_names())]

    def push_scope(self):
        self.names.append(set())

    def pop_scope(self):
        self.names.pop()

    def is_name_used(self, name):
        for scope in self.names:
            if name in scope:
                return True

        return False

    def visit_BitfieldAssignment(self, bitfield_assignment):
        return bitfield_assignment

    def visit_EnumDefinition(self, enum_definition):
        self.names[-1].add(enum_definition.name)

        for name, value in enum_definition.members:
            self.names[-1].add(name)

        return enum_definition

    def visit_BitfieldDefinition(self, bitfield_definition):
        self.names[-1].add(bitfield_definition.name)

        return bitfield_definition

    def visit_FunctionDefinition(self, function_def):
        self.names[-1].add(function_def.name)

        return self.generic_visit(function_def)

    def visit_Assignment(self, assignment):
        if assignment.declare is False:
            assignment.declare = not self.is_name_used(assignment.variable.name)

        if assignment.declare is True:
            self.names[-1].add(assignment.variable.name)

        return assignment
