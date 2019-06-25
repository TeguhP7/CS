from strings_with_arrows import *
import string
import os
import math
import Lexer
import Pharser

class Function(Pharser.BaseFunction):
  def __init__(self, name, body_node, arg_names):
    super().__init__(name)
    self.body_node = body_node
    self.arg_names = arg_names

  def execute(self, args):
    res = Pharser.RTResult()
    interpreter = Interpreter()
    exec_ctx = self.generate_new_context()

    res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
    if res.error: return res

    value = res.register(interpreter.visit(self.body_node, exec_ctx))
    if res.error: return res
    return res.success(value)

  def copy(self):
    copy = Function(self.name, self.body_node, self.arg_names)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<function {self.name}>"

class BuiltInFunction(Pharser.BaseFunction):
  def __init__(self, name):
    super().__init__(name)

  def execute(self, args):
    res = Pharser.RTResult()
    exec_ctx = self.generate_new_context()

    method_name = f'execute_{self.name}'
    method = getattr(self, method_name, self.no_visit_method)

    res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
    if res.error: return res

    return_value = res.register(method(exec_ctx))
    if res.error: return res
    return res.success(return_value)
  
  def no_visit_method(self, node, context):
    raise Exception(f'No execute_{self.name} method defined')

  def copy(self):
    copy = BuiltInFunction(self.name)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<built-in function {self.name}>"

  #####################################

  def execute_print(self, exec_ctx):
    print(str(exec_ctx.symbol_table.get('value')))
    return Pharser.RTResult().success(Pharser.Number.null)
  execute_print.arg_names = ['value']
  
  def execute_print_ret(self, exec_ctx):
    return Pharser.RTResult().success(Pharser.String(str(exec_ctx.symbol_table.get('value'))))
  execute_print_ret.arg_names = ['value']
  
  def execute_input(self, exec_ctx):
    text = input()
    return Pharser.RTResult().success(Pharser.String(text))
  execute_input.arg_names = []

  def execute_input_int(self, exec_ctx):
    while True:
      text = input()
      try:
        number = int(text)
        break
      except ValueError:
        print(f" Sajak '{text}' harus berupa bilangan bulat. Coba lagi yaa :) \n '{text}' (must be an integer. Try again!)")
    return Pharser.RTResult().success(Pharser.Number(number))
  execute_input_int.arg_names = []

  def execute_clear(self, exec_ctx):
    os.system('cls' if os.name == 'nt' else 'cls') 
    return Pharser.RTResult().success(Pharser.Number.null)
  execute_clear.arg_names = []

  def execute_is_number(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Pharser.Number)
    return Pharser.RTResult().success(Pharser.Number.true if is_number else Pharser.Number.false)
  execute_is_number.arg_names = ["value"]

  def execute_is_string(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Pharser.String)
    return Pharser.RTResult().success(Pharser.Number.true if is_number else Pharser.Number.false)
  execute_is_string.arg_names = ["value"]

  def execute_is_list(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Pharser.List)
    return Pharser.RTResult().success(Pharser.Number.true if is_number else Pharser.Number.false)
  execute_is_list.arg_names = ["value"]

  def execute_is_function(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Pharser.BaseFunction)
    return Pharser.RTResult().success(Pharser.Number.true if is_number else Pharser.Number.false)
  execute_is_function.arg_names = ["value"]

  def execute_append(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    value = exec_ctx.symbol_table.get("value")

    if not isinstance(list_, Pharser.List):
      return Pharser.RTResult().failure(Lexer.RTError(
        self.pos_start, self.pos_end,
        "Argumen pertama harus sebuah list \n(First argument must be list)",
        exec_ctx
      ))

    list_.elements.append(value)
    return Pharser.RTResult().success(Pharser.Number.null)
  execute_append.arg_names = ["list", "value"]

  def execute_pop(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")

    if not isinstance(list_, Pharser.List):
      return Pharser.RTResult().failure(Lexer.RTError(
        self.pos_start, self.pos_end,
        "Argumen pertama harus sebuah list \n(First argument must be list)",
        exec_ctx
      ))

    if not isinstance(index, Pharser.Number):
      return Pharser.RTResult().failure(Lexer.RTError(
        self.pos_start, self.pos_end,
        "Argumen kedua harus angka \n(Second argument must be number)",
        exec_ctx
      ))

    try:
      element = list_.elements.pop(index.value)
    except:
      return Pharser.RTResult().failure(Lexer.RTError(
        self.pos_start, self.pos_end,
        ' Sajak elemen pada indeks ini tidak dapat dihapus dari daftar ingatan, karena indeks di luar batas rindu \n(Element at this index could not be removed from list because index is out of bounds)',
        exec_ctx
      ))
    return Pharser.RTResult().success(element)
  execute_pop.arg_names = ["list", "index"]

  def execute_extend(self, exec_ctx):
    listA = exec_ctx.symbol_table.get("listA")
    listB = exec_ctx.symbol_table.get("listB")

    if not isinstance(listA, Pharser.List):
      return Pharser.RTResult().failure(Lexer.RTError(
        self.pos_start, self.pos_end,
        "Argumen pertama harus sebuah list \n(First argument must be list)",
        exec_ctx
      ))

    if not isinstance(listB, Pharser.List):
      return Pharser.RTResult().failure(Lexer.RTError(
        self.pos_start, self.pos_end,
        "Argumen kedua harus sebuah list \n(First argument must be list)",
        exec_ctx
      ))

    listA.elements.extend(listB.elements)
    return Pharser.RTResult().success(Pharser.Number.null)
  execute_extend.arg_names = ["listA", "listB"]

BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.print_ret   = BuiltInFunction("print_ret")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.input_int   = BuiltInFunction("input_int")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.is_number   = BuiltInFunction("is_number")
BuiltInFunction.is_string   = BuiltInFunction("is_string")
BuiltInFunction.is_list     = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.extend      = BuiltInFunction("extend")

#######################################
# CONTEXT
#######################################

class Context:
  def __init__(self, display_name, parent=None, parent_entry_pos=None):
    self.display_name = display_name
    self.parent = parent
    self.parent_entry_pos = parent_entry_pos
    self.symbol_table = None

#######################################
# SYMBOL TABLE
#######################################

class SymbolTable:
  def __init__(self, parent=None):
    self.symbols = {}
    self.parent = parent

  def get(self, name):
    value = self.symbols.get(name, None)
    if value == None and self.parent:
      return self.parent.get(name)
    return value

  def set(self, name, value):
    self.symbols[name] = value

  def remove(self, name):
    del self.symbols[name]

#######################################
# INTERPRETER
#######################################

class Interpreter:
  def visit(self, node, context):
    method_name = f'visit_{type(node).__name__}'
    method = getattr(self, method_name, self.no_visit_method)
    return method(node, context)

  def no_visit_method(self, node, context):
    raise Exception(f'No visit_{type(node).__name__} method defined')

  ###################################

  def visit_NumberNode(self, node, context):
    return Pharser.RTResult().success(
      Pharser.Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_StringNode(self, node, context):
    return Pharser.RTResult().success(
      Pharser.String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_ListNode(self, node, context):
    res = Pharser.RTResult()
    elements = []

    for element_node in node.element_nodes:
      elements.append(res.register(self.visit(element_node, context)))
      if res.error: return res

    return res.success(
      Pharser.List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_VarAccessNode(self, node, context):
    res = Pharser.RTResult()
    var_name = node.var_name_tok.value
    value = context.symbol_table.get(var_name)

    if not value:
      return res.failure(Lexer.RTError(
        node.pos_start, node.pos_end,
        f"Sajak '{var_name}' tak terdefinisi \n'{var_name}' is not defined",
        context
      ))

    value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
    return res.success(value)

  def visit_VarAssignNode(self, node, context):
    res = Pharser.RTResult()
    var_name = node.var_name_tok.value
    value = res.register(self.visit(node.value_node, context))
    if res.error: return res

    context.symbol_table.set(var_name, value)
    return res.success(value)

  def visit_BinOpNode(self, node, context):
    res = Pharser.RTResult()
    left = res.register(self.visit(node.left_node, context))
    if res.error: return res
    right = res.register(self.visit(node.right_node, context))
    if res.error: return res

    if node.op_tok.type == Lexer.TT_PLUS:
      result, error = left.added_to(right)
    elif node.op_tok.type == Lexer.TT_MINUS:
      result, error = left.subbed_by(right)
    elif node.op_tok.type == Lexer.TT_MUL:
      result, error = left.multed_by(right)
    elif node.op_tok.type == Lexer.TT_DIV:
      result, error = left.dived_by(right)
    elif node.op_tok.type == Lexer.TT_POW:
      result, error = left.powed_by(right)
    elif node.op_tok.type == Lexer.TT_EE:
      result, error = left.get_comparison_eq(right)
    elif node.op_tok.type == Lexer.TT_NE:
      result, error = left.get_comparison_ne(right)
    elif node.op_tok.type == Lexer.TT_LT:
      result, error = left.get_comparison_lt(right)
    elif node.op_tok.type == Lexer.TT_GT:
      result, error = left.get_comparison_gt(right)
    elif node.op_tok.type == Lexer.TT_LTE:
      result, error = left.get_comparison_lte(right)
    elif node.op_tok.type == Lexer.TT_GTE:
      result, error = left.get_comparison_gte(right)
    elif node.op_tok.matches(Lexer.TT_KEYWORD, 'Dan_waktu'):
      result, error = left.anded_by(right)
    elif node.op_tok.matches(Lexer.TT_KEYWORD, 'Atau_kita'):
      result, error = left.ored_by(right)

    if error:
      return res.failure(error)
    else:
      return res.success(result.set_pos(node.pos_start, node.pos_end))

  def visit_UnaryOpNode(self, node, context):
    res = Pharser.RTResult()
    number = res.register(self.visit(node.node, context))
    if res.error: return res

    error = None

    if node.op_tok.type == Lexer.TT_MINUS:
      number, error = number.multed_by(Pharser.Number(-1))
    elif node.op_tok.matches(Lexer.TT_KEYWORD, 'Tak_dapat'):
      number, error = number.notted()

    if error:
      return res.failure(error)
    else:
      return res.success(number.set_pos(node.pos_start, node.pos_end))

  def visit_IfNode(self, node, context):
    res = Pharser.RTResult()

    for condition, expr in node.cases:
      condition_value = res.register(self.visit(condition, context))
      if res.error: return res

      if condition_value.is_true():
        expr_value = res.register(self.visit(expr, context))
        if res.error: return res
        return res.success(expr_value)

    if node.else_case:
      else_value = res.register(self.visit(node.else_case, context))
      if res.error: return res
      return res.success(else_value)

    return res.success(None)

  def visit_ForNode(self, node, context):
    res = Pharser.RTResult()
    elements = []

    start_value = res.register(self.visit(node.start_value_node, context))
    if res.error: return res

    end_value = res.register(self.visit(node.end_value_node, context))
    if res.error: return res

    if node.step_value_node:
      step_value = res.register(self.visit(node.step_value_node, context))
      if res.error: return res
    else:
      step_value = Pharser.Number(1)

    i = start_value.value

    if step_value.value >= 0:
      condition = lambda: i < end_value.value
    else:
      condition = lambda: i > end_value.value
    
    while condition():
      context.symbol_table.set(node.var_name_tok.value, Pharser.Number(i))
      i += step_value.value

      elements.append(res.register(self.visit(node.body_node, context)))
      if res.error: return res

    return res.success(
      Pharser.List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_WhileNode(self, node, context):
    res = Pharser.RTResult()
    elements = []

    while True:
      condition = res.register(self.visit(node.condition_node, context))
      if res.error: return res

      if not condition.is_true(): break

      elements.append(res.register(self.visit(node.body_node, context)))
      if res.error: return res

    return res.success(
      Pharser.List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_FuncDefNode(self, node, context):
    res = Pharser.RTResult()

    func_name = node.var_name_tok.value if node.var_name_tok else None
    body_node = node.body_node
    arg_names = [arg_name.value for arg_name in node.arg_name_toks]
    func_value = Function(func_name, body_node, arg_names).set_context(context).set_pos(node.pos_start, node.pos_end)
    
    if node.var_name_tok:
      context.symbol_table.set(func_name, func_value)

    return res.success(func_value)

  def visit_CallNode(self, node, context):
    res = Pharser.RTResult()
    args = []

    value_to_call = res.register(self.visit(node.node_to_call, context))
    if res.error: return res
    value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

    for arg_node in node.arg_nodes:
      args.append(res.register(self.visit(arg_node, context)))
      if res.error: return res

    return_value = res.register(value_to_call.execute(args))
    if res.error: return res
    return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
    return res.success(return_value)

#######################################
# RUN
#######################################

global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Pharser.Number.null)
global_symbol_table.set("Salah", Pharser.Number.false)
global_symbol_table.set("Benar", Pharser.Number.true)
global_symbol_table.set("MATH_PI", Pharser.Number.math_PI)
global_symbol_table.set("Sajakku", BuiltInFunction.print)
global_symbol_table.set("Sajakku_RET", BuiltInFunction.print_ret)
global_symbol_table.set("Masukkan", BuiltInFunction.input)
global_symbol_table.set("Masukkan_INT", BuiltInFunction.input_int)
global_symbol_table.set("Tinggal_Kenangan", BuiltInFunction.clear)
global_symbol_table.set("CLS", BuiltInFunction.clear)
global_symbol_table.set("Engkau_NUM", BuiltInFunction.is_number)
global_symbol_table.set("Engkau_STR", BuiltInFunction.is_string)
global_symbol_table.set("Engkau_LIST", BuiltInFunction.is_list)
global_symbol_table.set("Engkau_FUN", BuiltInFunction.is_function)
global_symbol_table.set("Tambahkan", BuiltInFunction.append)
global_symbol_table.set("Keluarkan", BuiltInFunction.pop)
global_symbol_table.set("Gabung", BuiltInFunction.extend)

def run(fn, text):

  # Generate tokens
  lexer = Lexer.Lexer(fn, text)
  tokens, error = lexer.make_tokens()
  if error: return None, error
  
  # Generate AST
  parser = Pharser.Parser(tokens)
  ast = parser.parse()
  if ast.error: return None, ast.error

  # Run program
  interpreter = Interpreter()
  context = Context('<program>')
  context.symbol_table = global_symbol_table
  result = interpreter.visit(ast.node, context)

  return result.value, result.error