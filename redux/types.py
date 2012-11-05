from redux.autorepr import AutoRepr

class Type(AutoRepr):
    def __init__(self, name):
        super(Type, self).__init__()
        self.name = name

str_ = Type("str")
int_ = Type("int")
float_ = Type("float")
object_ = Type("object")

def is_numeric(type_):
    return type_ is int_ or type_ is float_
