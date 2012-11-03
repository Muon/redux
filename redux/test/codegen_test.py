from nose.tools import eq_
from redux.codegenerator import compile_script

def test_code_generation():
    code_examples = [
        ("if 2 > 1 else end", "if((2>1)){\n}\nelse {\n}"),
        ("while 2 > 1 end", "while(1){\nif((2>1)){\n}\nelse {\nbreak;\n}\n}"),
        ("def f(a) return a end x = f(1)", "int __retval0 = 0;\n{\nint a = 1;\n__retval0 = a;\n}\nint x = __retval0;"),
        ("say(1, 2)", "say 1, 2;"),
        ("sqrt(2)", "(|/2);"),
        ("a = \"foo\" say(a)", "say \"foo\";"),
        ("a = 1 - 1", "int a = (1-1);"),
        ("a = 1 + 1", "int a = (1+1);"),
        ("a = 1 * 1", "int a = (1*1);"),
        ("a = 1 / 1", "int a = (1/1);"),
        ("a = 1 > 1", "int a = (1>1);"),
        ("a = 1 < 1", "int a = (1<1);"),
        ("a = 1 <= 1", "int a = (1<=1);"),
        ("a = 1 >= 1", "int a = (1>=1);"),
        ("a = 1 == 1", "int a = (1==1);"),
        ("a = 1 != 1", "int a = (1!=1);"),
        ("a = 1 and 1", "int a = (1&&1);"),
        ("a = 1 or 1", "int a = (1||1);"),
        ("a = not 1", "int a = (!1);"),
        ("a = 1.0 b = 1 + a", "float a = 1.0;\nfloat b = (1+a);"),
    ]

    for redux_code, rescript_code in code_examples:
        yield check_code_generation, redux_code, ("{\n" + rescript_code + "\n}\n")

def check_code_generation(redux_code, rescript_code):
    eq_(compile_script("codegen_test", redux_code), rescript_code)
