from .common import (
   Token,
   TokenType,
   TokenLang,
   FindNext,
)

from .extract import (
   TokenExtract,
   TokenExtractEnv,
   ExtractQuote,
   MergeSymUnderline,
   MarkLineNumber,
)
from .decorate import \
   TokenScope,        \
   TokenDecorate,     \
   TokenDecorateEnv


def _MergeIndent(env, out):
   if env.i != 0 and env.GetToken(env.i-1) != '\n':
      # mark as space
      t = Token(env.GetToken(env.i), TokenType.SPACE, env.L, env.C)
      out.append(t)
      env.i += 1
      env.C += 1
      return True
   # mark as indent
   L = env.L
   C = env.C
   t = Token(env.GetToken(env.i), TokenType.INDENT, L, C)
   count = 1
   for i in range(env.i+1, env.n):
      token = env.GetToken(i)
      if token == ' ':
         t.N += token
         count += 1
         C += 1
      elif token == '\t':
         t.N += token
         count += 8
         C += 1
      else:
         break
   t.data = count
   env.i += len(t.N)
   out.append(t)
   env.C = C
   return True

def _ExtractTriquote(env, out):
   start_token = env.GetToken(env.i)
   skip = False
   tri = 1
   L = env.L
   C = env.C
   if env.i+2 >= env.n or env.GetToken(env.i+1) != start_token or env.GetToken(env.i+2) != start_token:
      return False
   t = Token(start_token*3, TokenType.STRING, L, C)
   for i in range(env.i+3, env.n):
      token = env.GetToken(i)
      if token == '\n':
         L += 1
         C = 0
      t.N += token
      C += len(token)
      if skip:
         skip = False
         continue
      if token == '\\':
         skip = True
      elif token == start_token:
         if i+2 < env.n and env.GetToken(i+1) == start_token or env.GetToken(i+2) == start_token:
            t.N += start_token * 2
            env.L = L
            env.C = C+2
            env.i = i+3
            out.append(t)
            return True
   env.L = L
   env.C = C
   env.i = env.n
   out.append(t)
   return True


def _ExtractLineComment(env, out):
   C = env.C
   t = Token('#', TokenType.COMMENT, env.L, C)
   out.append(t)
   env.i += 1
   for i in range(env.i, env.n):
      token = env.GetToken(i)
      if token == '\n':
         break
      else:
         t.N += token
         C += len(token)
         env.i += 1
   env.C += C - env.C
   env.i += 1
   return True


extract_map_root = {
   # TODO: f-string and r-string
   "'": [_ExtractTriquote, ExtractQuote],
   '"': [_ExtractTriquote, ExtractQuote],
   "#": [_ExtractLineComment],
   " ": [_MergeIndent],
   "\t": [_MergeIndent],
   "\n": [MarkLineNumber],
   "_": [MergeSymUnderline],
}


def Extract(tokens):
   env = TokenExtractEnv(tokens, extract_map_root)
   return TokenExtract(env)


def _DecorateFrom(env, scope):
   t0 = env.GetToken(env.i)
   data = {}
   t = Token("import", TokenType.BLOCK, t0.L, t0.C, TokenLang.PYTHON, 2000, data=data)
   data_path = []
   data["path"] = data_path
   for i in range(env.i+1, env.n):
      token = env.GetToken(i)
      if token.N == 'import':
         env.i = i+1
         break
      if token.T != TokenType.SPACE:
         data_path.append(token)
   return _DecorateImport(env, scope, t)


def _DecorateImport(env, scope, t=None):
   if not t:
      t0 = env.GetToken(env.i)
      t = Token("import", TokenType.BLOCK, t0.L, t0.C, TokenLang.PYTHON, 2000, data={})
   data = t.data
   bracket = 0
   escbr = 0
   data_sym = []
   data["sym"] = data_sym
   for i in range(env.i+1, env.n):
      token = env.GetToken(i)
      if token.T == TokenType.BR:
         if bracket == 0 and escbr == 0:
            env.i = i+1
            break
         escbr = 0
      if token.N == '(':
         bracket += 1
         continue
      elif token.N == ')':
         bracket -= 1
         continue
      elif token.N == '\\': # TODO: check [\\ \n]
         escbr = 1
         continue
      if (
         token.T != TokenType.SPACE and
         token.T != TokenType.BR and
         token.T != TokenType.INDENT and
         token.T != TokenType.COMMENT
      ):
         data_sym.append(token)
   scope.tokens.append(t)
   return True


bracket_pairs = {"(": ")", "[": "]", "{": "}",}
def _FindBracketEnd(env, i):
   left = bracket_pairs.keys()
   right = bracket_pairs.values()
   bstack = [bracket_pairs[env.GetToken(i).N]]
   for j in range(i+1, env.n):
      token = env.GetToken(j)
      if token.N in left:
         bstack.append(bracket_pairs[token.N])
      elif token.N in right:
         if bstack[-1] == token.N:
            bstack.pop()
         else:
            # TODO: bracket miss match
            return j+1
         if len(bstack) == 0:
            return j+1
   return env.n


def _IsEmptyLine(env, i):
   empty = True
   for j in range(i+1, env.n):
      token = env.GetToken(j)
      if token.N == '\n':
         return True, j+1
      if token.T == TokenType.SPACE:
         continue
      if token.T == TokenType.BR:
         continue
      if token.T == TokenType.INDENT:
         continue
      if token.T == TokenType.COMMENT:
         continue
      if token.T == TokenType.STRING:
         continue
      return False, i
   return True, env.n


def _GetScopeJ(env, i):
   # TODO: pick ahead @annotations
   #       now we assume @annotation is a BLOCK
   # examples:
   # - print \ \n ("hello")
   # - if (True or \n False): ...
   # above no need indent after \n
   j = i+1
   bracket_left = bracket_pairs.keys()
   while j < env.n:
      token = env.GetToken(j)
      if token.N in bracket_left:
         j = _FindBracketEnd(env, j)
         continue
      if token.N == '\\': # \ \n
         j += 2
         continue
      if token.N == '\n':
         j += 1
         break
      j += 1
   indent_base = -1
   while j < env.n:
      is_empty_line, nextj = _IsEmptyLine(env, j)
      if is_empty_line:
         j = nextj
         continue

      token = env.GetToken(j)
      if indent_base < 0 and token.T == TokenType.INDENT:
         indent_base = token.data
         j += 1
      elif (token.T == TokenType.INDENT and indent_base > token.data) or token.T != TokenType.INDENT:
         return j-1

      while j < env.n:
         token = env.GetToken(j)
         if token.N in bracket_left:
            j = _FindBracketEnd(env, j)
         elif token.N == '\\':
            j += 2
         elif token.N == '\n':
            j += 1
            break
         else:
            j += 1
   return env.n

def _DecorateClass(env, scope):
   j = _GetScopeJ(env, env.i)
   token = env.GetToken(env.i)
   subscope = TokenDecorate(env, env.i+1, j-1)
   class_data = { "children": subscope.tokens }
   t = Token("class", TokenType.KLASS, token.L, token.C, TokenLang.PYTHON, 2, data=class_data)
   scope.tokens.append(t)
   env.i = j


decorate_map_root = {
   # TODO: __import__
   "from": [_DecorateFrom],
   "import": [_DecorateImport],
   # TODO: @annotation
   "class": [_DecorateClass],
   "def": [],
   "if": [],
   "elif": [],
   "else": [],
   "while": [],
   "for": [],
   "with": [],
}


def Decorate(tokens):
   env = TokenDecorateEnv(tokens, decorate_map_root)
   return TokenDecorate(env).tokens


if __name__ == "__main__":
   import os
   import sys
   from .common import TokenizeText
   filepath = sys.argv[1]
   with open(filepath, 'r') as f:
      code = f.read()
   tokens = Extract(TokenizeText(code))

   L = []
   for token in tokens:
      if len(L) == 0:
         L.append(token)
      elif token.L == L[-1].L:
         L.append(token)
      else:
         print(L[-1].L, L)
         L = [token]
   if len(L) > 0: print(L[-1].L, L)

   print('-----------------------------')
   tree = Decorate(tokens)
   for token in tree:
      print(token.L, token.C, token, token.data)
