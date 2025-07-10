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
from .decorate import (
   TokenDecorate,
   TokenDecorateEnv,
)

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
   count = 0
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
   t = Token(start_token*3, TokenType.CONST, L, C)
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
   t = Token("import", TokenType.BLOCK, t0.L, t0.C, TokenLang.PYTHON, 2000, data=[])
   for i in range(env.i+1, env.n):
      token = env.GetToken(i)
      if token.N == 'import':
         env.i = i+1
         break
      t.data.append(token)
   return _DecorateImport(env, scope, t)


def _DecorateImport(env, scope, t=None):
   if not t:
      t0 = env.GetToken(env.i)
      t = Token("import", TokenType.BLOCK, t0.L, t0.C, TokenLang.PYTHON, 2000, data=[])
   bracket = 0
   for i in range(env.i+1, env.n):
      token = env.GetToken(i)
      if token.N == '\n' and bracket == 0:
         env.i = i+1
         break
      t.data.append(token)
      if token.N == '(':
         bracket += 1
      elif token.N == ')':
         bracket -= 1
   scope.tokens.append(t)
   return True, False, False


decorate_map_root = {
   "from": [_DecorateFrom],
   "import": [_DecorateImport],
   "class": [],
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
   return TokenDecorate(env)


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
