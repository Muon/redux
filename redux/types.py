str_ = ("str",)
int_ = ("int",)
float_ = ("float",)
object_ = ("object",)


def is_numeric(type_):
    return type_ is int_ or type_ is float_


def common_arithmetic_type(type_a, type_b):
    assert is_numeric(type_a)
    assert is_numeric(type_b)

    if type_a is int_ and type_b is int_:
        return int_
    else:
        return float_


def check_assignable(expr_type, var_type):
    assert expr_type is not None
    assert var_type is not None

    if var_type is str_:
        return False

    return (expr_type is var_type) or \
           (is_numeric(expr_type) and is_numeric(var_type))
