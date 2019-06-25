from strings_with_arrows import *
import math
import string
import os
import Lexer
import main

#######################################
# PARSE RESULT
#######################################

class ParseResult:
  def __init__(self):
    self.error = None
    self.node = None
    self.last_registered_advance_count = 0
    self.advance_count = 0

  def register_advancement(self):
    self.last_registered_advance_count = 1
    self.advance_count += 1

  def register(self, res):
    self.last_registered_advance_count = res.advance_count
    self.advance_count += res.advance_count
    if res.error: self.error = res.error
    return res.node

  def success(self, node):
    self.node = node
    return self

  def failure(self, error):
    if not self.error or self.last_registered_advance_count == 0:
      self.error = error
    return self

#######################################
# PARSER
#######################################

class Parser:
  def __init__(self, tokens):
    self.tokens = tokens
    self.tok_idx = -1
    self.advance()

  def advance(self, ):
    self.tok_idx += 1
    if self.tok_idx < len(self.tokens):
      self.current_tok = self.tokens[self.tok_idx]
    return self.current_tok

  def parse(self):
    res = self.expr()
    if not res.error and self.current_tok.type != Lexer.TT_EOF:
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Mengharapkan seperti (senja kala itu) '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'Dan_waktu' or 'Atau'"
      ))
    return res

  ###################################

  def expr(self):
    res = ParseResult()

    if self.current_tok.matches(Lexer.TT_KEYWORD, 'Sajak'):
      res.register_advancement()
      self.advance()

      if self.current_tok.type != Lexer.TT_IDENTIFIER:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Mengharapkan seperti (senja kala itu) identifier"
        ))

      var_name = self.current_tok
      res.register_advancement()
      self.advance()

      if self.current_tok.type != Lexer.TT_EQ:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Mengharapkan seperti (senja kala itu) '='"
        ))

      res.register_advancement()
      self.advance()
      expr = res.register(self.expr())
      if res.error: return res
      return res.success(Lexer.VarAssignNode(var_name, expr))

    node = res.register(self.bin_op(self.comp_expr, ((Lexer.TT_KEYWORD, 'Dan_waktu'), (Lexer.TT_KEYWORD, 'Atau'))))

    if res.error:
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Mengharapkan seperti (senja kala itu) 'Sajak', 'Ketika_nada', 'Untuk_kita', 'Sedangkan', 'Fungsi', int, float, identifier, '+', '-', '(', '[' or 'Tak_dapat'"
      ))

    return res.success(node)

  def comp_expr(self):
    res = ParseResult()

    if self.current_tok.matches(Lexer.TT_KEYWORD, 'Tak_dapat'):
      op_tok = self.current_tok
      res.register_advancement()
      self.advance()

      node = res.register(self.comp_expr())
      if res.error: return res
      return res.success(Lexer.UnaryOpNode(op_tok, node))
    
    node = res.register(self.bin_op(self.arith_expr, (Lexer.TT_EE, Lexer.TT_NE, Lexer.TT_LT, Lexer.TT_GT, Lexer.TT_LTE, Lexer.TT_GTE)))
    
    if res.error:
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Mengharapkan seperti (senja kala itu) int, float, identifier, '+', '-', '(', '[', 'Ketika_nada', 'Untuk_kita', 'Sedangkan', 'Fungsi' or 'Tak_dapat'"
      ))

    return res.success(node)

  def arith_expr(self):
    return self.bin_op(self.term, (Lexer.TT_PLUS, Lexer.TT_MINUS))

  def term(self):
    return self.bin_op(self.factor, (Lexer.TT_MUL, Lexer.TT_DIV))

  def factor(self):
    res = ParseResult()
    tok = self.current_tok

    if tok.type in (Lexer.TT_PLUS, Lexer.TT_MINUS):
      res.register_advancement()
      self.advance()
      factor = res.register(self.factor())
      if res.error: return res
      return res.success(Lexer.UnaryOpNode(tok, factor))

    return self.power()

  def power(self):
    return self.bin_op(self.call, (Lexer.TT_POW, ), self.factor)

  def call(self):
    res = ParseResult()
    atom = res.register(self.atom())
    if res.error: return res

    if self.current_tok.type == Lexer.TT_LPAREN:
      res.register_advancement()
      self.advance()
      arg_nodes = []

      if self.current_tok.type == Lexer.TT_RPAREN:
        res.register_advancement()
        self.advance()
      else:
        arg_nodes.append(res.register(self.expr()))
        if res.error:
          return res.failure(Lexer.InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Mengharapkan seperti (senja kala itu) ')', 'Sajak', 'Ketika_nada', 'Untuk_kita', 'Sedangkan', 'Fungsi', int, float, identifier, '+', '-', '(', '[' or 'Tak_dapat'"
          ))

        while self.current_tok.type == Lexer.TT_COMMA:
          res.register_advancement()
          self.advance()

          arg_nodes.append(res.register(self.expr()))
          if res.error: return res

        if self.current_tok.type != Lexer.TT_RPAREN:
          return res.failure(Lexer.InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            f"Mengharapkan seperti (senja kala itu) ',' or ')'"
          ))

        res.register_advancement()
        self.advance()
      return res.success(Lexer.CallNode(atom, arg_nodes))
    return res.success(atom)

  def atom(self):
    res = ParseResult()
    tok = self.current_tok

    if tok.type in (Lexer.TT_INT, Lexer.TT_FLOAT):
      res.register_advancement()
      self.advance()
      return res.success(Lexer.NumberNode(tok))

    elif tok.type == Lexer.TT_STRING:
      res.register_advancement()
      self.advance()
      return res.success(Lexer.StringNode(tok))

    elif tok.type == Lexer.TT_IDENTIFIER:
      res.register_advancement()
      self.advance()
      return res.success(Lexer.VarAccessNode(tok))

    elif tok.type == Lexer.TT_LPAREN:
      res.register_advancement()
      self.advance()
      expr = res.register(self.expr())
      if res.error: return res
      if self.current_tok.type == Lexer.TT_RPAREN:
        res.register_advancement()
        self.advance()
        return res.success(expr)
      else:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Mengharapkan seperti (senja kala itu) ')'"
        ))

    elif tok.type == Lexer.TT_LSQUARE:
      list_expr = res.register(self.list_expr())
      if res.error: return res
      return res.success(list_expr)
    
    elif tok.matches(Lexer.TT_KEYWORD, 'Ketika_nada'):
      if_expr = res.register(self.if_expr())
      if res.error: return res
      return res.success(if_expr)

    elif tok.matches(Lexer.TT_KEYWORD, 'Untuk_kita'):
      for_expr = res.register(self.for_expr())
      if res.error: return res
      return res.success(for_expr)

    elif tok.matches(Lexer.TT_KEYWORD, 'Sedangkan'):
      while_expr = res.register(self.while_expr())
      if res.error: return res
      return res.success(while_expr)

    elif tok.matches(Lexer.TT_KEYWORD, 'Fungsi'):
      func_def = res.register(self.func_def())
      if res.error: return res
      return res.success(func_def)

    return res.failure(Lexer.InvalidSyntaxError(
      tok.pos_start, tok.pos_end,
      "Mengharapkan seperti (senja kala itu) int, float, identifier, '+', '-', '(', '[', 'Ketika_nada', 'Untuk_kita', 'Sedangkan', 'Fungsi'"
    ))

  def list_expr(self):
    res = ParseResult()
    element_nodes = []
    pos_start = self.current_tok.pos_start.copy()

    if self.current_tok.type != Lexer.TT_LSQUARE:
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) '['"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == Lexer.TT_RSQUARE:
      res.register_advancement()
      self.advance()
    else:
      element_nodes.append(res.register(self.expr()))
      if res.error:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Mengharapkan seperti (senja kala itu) ']', 'Sajak', 'Ketika_nada', 'Untuk_kita', 'Sedangkan', 'Fungsi', int, float, identifier, '+', '-', '(', '[' or 'Tak_dapat'"
        ))

      while self.current_tok.type == Lexer.TT_COMMA:
        res.register_advancement()
        self.advance()

        element_nodes.append(res.register(self.expr()))
        if res.error: return res

      if self.current_tok.type != Lexer.TT_RSQUARE:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Mengharapkan seperti (senja kala itu) ',' or ']'"
        ))

      res.register_advancement()
      self.advance()

    return res.success(Lexer.ListNode(
      element_nodes,
      pos_start,
      self.current_tok.pos_end.copy()
    ))

  def if_expr(self):
    res = ParseResult()
    cases = []
    else_case = None

    if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Ketika_nada'):
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) 'Ketika_nada'"
      ))

    res.register_advancement()
    self.advance()

    condition = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Maka_cakrawala'):
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) 'Maka_cakrawala'"
      ))

    res.register_advancement()
    self.advance()

    expr = res.register(self.expr())
    if res.error: return res
    cases.append((condition, expr))

    while self.current_tok.matches(Lexer.TT_KEYWORD, 'Lain_jika'):
      res.register_advancement()
      self.advance()

      condition = res.register(self.expr())
      if res.error: return res

      if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Maka_cakrawala'):
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Mengharapkan seperti (senja kala itu) 'Maka_cakrawala'"
        ))

      res.register_advancement()
      self.advance()

      expr = res.register(self.expr())
      if res.error: return res
      cases.append((condition, expr))

    if self.current_tok.matches(Lexer.TT_KEYWORD, 'Lainnya'):
      res.register_advancement()
      self.advance()

      else_case = res.register(self.expr())
      if res.error: return res

    return res.success(Lexer.IfNode(cases, else_case))

  def for_expr(self):
    res = ParseResult()

    if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Untuk_kita'):
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) 'Untuk_kita'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type != Lexer.TT_IDENTIFIER:
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) identifier"
      ))

    var_name = self.current_tok
    res.register_advancement()
    self.advance()

    if self.current_tok.type != Lexer.TT_EQ:
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) '='"
      ))
    
    res.register_advancement()
    self.advance()

    start_value = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Ke'):
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) 'Ke'"
      ))
    
    res.register_advancement()
    self.advance()

    end_value = res.register(self.expr())
    if res.error: return res

    if self.current_tok.matches(Lexer.TT_KEYWORD, 'Melangkah'):
      res.register_advancement()
      self.advance()

      step_value = res.register(self.expr())
      if res.error: return res
    else:
      step_value = None

    if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Maka_cakrawala'):
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) 'Maka_cakrawala'"
      ))

    res.register_advancement()
    self.advance()

    body = res.register(self.expr())
    if res.error: return res

    return res.success(Lexer.ForNode(var_name, start_value, end_value, step_value, body))

  def while_expr(self):
    res = ParseResult()

    if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Sedangkan'):
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) 'Sedangkan'"
      ))

    res.register_advancement()
    self.advance()

    condition = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Maka_cakrawala'):
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) 'Maka_cakrawala'"
      ))

    res.register_advancement()
    self.advance()

    body = res.register(self.expr())
    if res.error: return res

    return res.success(Lexer.WhileNode(condition, body))

  def func_def(self):
    res = ParseResult()

    if not self.current_tok.matches(Lexer.TT_KEYWORD, 'Fungsi'):
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) 'Fungsi'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == Lexer.TT_IDENTIFIER:
      var_name_tok = self.current_tok
      res.register_advancement()
      self.advance()
      if self.current_tok.type != Lexer.TT_LPAREN:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Mengharapkan seperti (senja kala itu) '('"
        ))
    else:
      var_name_tok = None
      if self.current_tok.type != Lexer.TT_LPAREN:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Mengharapkan seperti (senja kala itu) identifier or '('"
        ))
    
    res.register_advancement()
    self.advance()
    arg_name_toks = []

    if self.current_tok.type == Lexer.TT_IDENTIFIER:
      arg_name_toks.append(self.current_tok)
      res.register_advancement()
      self.advance()
      
      while self.current_tok.type == Lexer.TT_COMMA:
        res.register_advancement()
        self.advance()

        if self.current_tok.type != Lexer.TT_IDENTIFIER:
          return res.failure(Lexer.InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            f"Mengharapkan seperti (senja kala itu) identifier"
          ))

        arg_name_toks.append(self.current_tok)
        res.register_advancement()
        self.advance()
      
      if self.current_tok.type != Lexer.TT_RPAREN:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Mengharapkan seperti (senja kala itu) ',' or ')'"
        ))
    else:
      if self.current_tok.type != Lexer.TT_RPAREN:
        return res.failure(Lexer.InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Mengharapkan seperti (senja kala itu) identifier or ')'"
        ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type != Lexer.TT_ARROW:
      return res.failure(Lexer.InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Mengharapkan seperti (senja kala itu) '->'"
      ))

    res.register_advancement()
    self.advance()
    node_to_return = res.register(self.expr())
    if res.error: return res

    return res.success(Lexer.FuncDefNode(
      var_name_tok,
      arg_name_toks,
      node_to_return
    ))

  ###################################

  def bin_op(self, func_a, ops, func_b=None):
    if func_b == None:
      func_b = func_a
    
    res = ParseResult()
    left = res.register(func_a())
    if res.error: return res

    while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
      op_tok = self.current_tok
      res.register_advancement()
      self.advance()
      right = res.register(func_b())
      if res.error: return res
      left = Lexer.BinOpNode(left, op_tok, right)

    return res.success(left)

#######################################
# RUNTIME RESULT
#######################################

class RTResult:
  def __init__(self):
    self.value = None
    self.error = None

  def register(self, res):
    self.error = res.error
    return res.value

  def success(self, value):
    self.value = value
    return self

  def failure(self, error):
    self.error = error
    return self

#######################################
# VALUES
#######################################

class Value:
  def __init__(self):
    self.set_pos()
    self.set_context()

  def set_pos(self, pos_start=None, pos_end=None):
    self.pos_start = pos_start
    self.pos_end = pos_end
    return self

  def set_context(self, context=None):
    self.context = context
    return self

  def added_to(self, other):
    return None, self.illegal_operation(other)

  def subbed_by(self, other):
    return None, self.illegal_operation(other)

  def multed_by(self, other):
    return None, self.illegal_operation(other)

  def dived_by(self, other):
    return None, self.illegal_operation(other)

  def powed_by(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_eq(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_ne(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_lt(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_gt(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_lte(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_gte(self, other):
    return None, self.illegal_operation(other)

  def anded_by(self, other):
    return None, self.illegal_operation(other)

  def ored_by(self, other):
    return None, self.illegal_operation(other)

  def notted(self):
    return None, self.illegal_operation(other)

  def execute(self, args):
    return RTResult().failure(self.illegal_operation())

  def copy(self):
    raise Exception('Tak ada metode penyalinan yang ditentukan ketika senja bersama\n(No copy method defined)')

  def is_true(self):
    return False

  def illegal_operation(self, other=None):
    if not other: other = self
    return Lexer.RTError(
      self.pos_start, other.pos_end,
      ' Engkau tak diperkenankan (Operasi illegal)',
      self.context
    )

class Number(Value):
  def __init__(self, value):
    super().__init__()
    self.value = value

  def added_to(self, other):
    if isinstance(other, Number):
      return Number(self.value + other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def subbed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value - other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value * other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def dived_by(self, other):
    if isinstance(other, Number):
      if other.value == 0:
        return None, Lexer.RTError(
          other.pos_start, other.pos_end,
          ' Engkau tak dapat didefinisikan \n(Wahai pujangga jangan engkau bagi dengan angka 0)',
          self.context
        )

      return Number(self.value / other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def powed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value ** other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_eq(self, other):
    if isinstance(other, Number):
      return Number(int(self.value == other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_ne(self, other):
    if isinstance(other, Number):
      return Number(int(self.value != other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_lt(self, other):
    if isinstance(other, Number):
      return Number(int(self.value < other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_gt(self, other):
    if isinstance(other, Number):
      return Number(int(self.value > other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_lte(self, other):
    if isinstance(other, Number):
      return Number(int(self.value <= other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_gte(self, other):
    if isinstance(other, Number):
      return Number(int(self.value >= other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def anded_by(self, other):
    if isinstance(other, Number):
      return Number(int(self.value and other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def ored_by(self, other):
    if isinstance(other, Number):
      return Number(int(self.value or other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def notted(self):
    return Number(1 if self.value == 0 else 0).set_context(self.context), None

  def copy(self):
    copy = Number(self.value)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy

  def is_true(self):
    return self.value != 0

  def __str__(self):
    return str(self.value)
  
  def __repr__(self):
    return str(self.value)

Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)
Number.math_PI = Number(math.pi)

class String(Value):
  def __init__(self, value):
    super().__init__()
    self.value = value

  def added_to(self, other):
    if isinstance(other, String):
      return String(self.value + other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, Number):
      return String(self.value * other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def is_true(self):
    return len(self.value) > 0

  def copy(self):
    copy = String(self.value)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy

  def __str__(self):
    return self.value

  def __repr__(self):
    return f'"{self.value}"'

class List(Value):
  def __init__(self, elements):
    super().__init__()
    self.elements = elements

  def added_to(self, other):
    new_list = self.copy()
    new_list.elements.append(other)
    return new_list, None

  def subbed_by(self, other):
    if isinstance(other, Number):
      new_list = self.copy()
      try:
        new_list.elements.pop(other.value)
        return new_list, None
      except:
        return None, Lexer.RTError(
          other.pos_start, other.pos_end,
          ' Sajak elemen pada indeks ini tidak dapat dihapus dari daftar ingatan, karena indeks di luar batas rindu \n(Element at this index could not be removed from list because index is out of bounds)',
          self.context
        )
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, List):
      new_list = self.copy()
      new_list.elements.extend(other.elements)
      return new_list, None
    else:
      return None, Value.illegal_operation(self, other)

  def dived_by(self, other):
    if isinstance(other, Number):
      try:
        return self.elements[other.value], None
      except:
        return None, Lexer.RTError(
          other.pos_start, other.pos_end,
          ' Sajak elemen pada indeks ini tidak dapat diambil dari daftar masa lalu, karena indeks di luar batas kenangan \n(Element at this index could not be retrieved from list because index is out of bounds)',
          self.context
        )
    else:
      return None, Value.illegal_operation(self, other)
  
  def copy(self):
    copy = List(self.elements)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy

  def __str__(self):
    return ", ".join([str(x) for x in self.elements])

  def __repr__(self):
    return f'[{", ".join([repr(x) for x in self.elements])}]'

class BaseFunction(Value):
  def __init__(self, name):
    super().__init__()
    self.name = name or "<anonymous>"

  def generate_new_context(self):
    new_context = main.Context(self.name, self.context, self.pos_start)
    new_context.symbol_table = main.SymbolTable(new_context.parent.symbol_table)
    return new_context

  def check_args(self, arg_names, args):
    res = RTResult()

    if len(args) > len(arg_names):
      return res.failure(Lexer.RTError(
        self.pos_start, self.pos_end,
        f"{len(args) - len(arg_names)} too many args passed into {self}",
        self.context
      ))
    
    if len(args) < len(arg_names):
      return res.failure(Lexer.RTError(
        self.pos_start, self.pos_end,
        f"{len(arg_names) - len(args)} too few args passed into {self}",
        self.context
      ))

    return res.success(None)

  def populate_args(self, arg_names, args, exec_ctx):
    for i in range(len(args)):
      arg_name = arg_names[i]
      arg_value = args[i]
      arg_value.set_context(exec_ctx)
      exec_ctx.symbol_table.set(arg_name, arg_value)

  def check_and_populate_args(self, arg_names, args, exec_ctx):
    res = RTResult()
    res.register(self.check_args(arg_names, args))
    if res.error: return res
    self.populate_args(arg_names, args, exec_ctx)
    return res.success(None)