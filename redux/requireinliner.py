import sys
from os import getcwd
from os.path import splitext
from redux.parser import parse
from redux.visitor import ASTTransformer, ASTVisitor


class RequireInliner(ASTTransformer):
    """Inlines the AST of files included with 'require'."""
    def visit_Require(self, require):
        base_filename, extension = splitext(require.path)

        if extension == ".redux":
            with open(require.path, "rt") as file_:
                code = file_.read()
        else:
            with open(require.path + ".redux", "rt") as file_:
                code = file_.read()

        ast_, errors = parse(code)
        if errors:
            for lineno, message in errors:
                sys.stderr.write("%s:%d: %s\n" % (require.path, lineno, message))
            raise RuntimeError
        else:
            class TopLevelCodeError(RuntimeError):
                pass

            class TopLevelCodeChecker(ASTVisitor):
                """Checks there is no top-level code in the required file."""
                def visit_FunctionDefinition(self, funcdef):
                    pass

                def visit_EnumDefinition(self, enumdef):
                    pass

                def visit_BitfieldDefinition(self, bitfielddef):
                    pass

                def visit_Require(self, require):
                    pass

                def visit_Stmt(self, stmt):
                    raise TopLevelCodeError(stmt)

            TopLevelCodeChecker().visit(ast_)
            self.visit(ast_)
            return ast_.statements
