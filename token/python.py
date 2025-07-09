from .common import Token, TokenType, TokenLang, TokenExtract, TokenExtractEnv, FindNext

def _MergeSym(env, out):
   return False

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


def _ExtractQuote(env, out):
   start_token = env.GetToken(env.i)
   skip = False
   L = env.L
   C = env.C
   t = Token(start_token, TokenType.CONST, L, C)
   for i in range(env.i+1, env.n):
      token = env.GetToken(i)
      if token == '\n':
         env.C = C
         out.append(t)
         env.i = i+1
         return True
      t.N += token
      C += len(token)
      if skip:
         skip = False
         continue
      if token == '\\':
         skip = True
      elif token == start_token:
         env.C = C
         out.append(t)
         env.i = i+1
         return True
   env.C = C
   out.append(t)
   env.i = env.n
   return True


extract_map_root = {
   "'": [_ExtractTriquote, _ExtractQuote],
   '"': [_ExtractTriquote, _ExtractQuote],
   "_": [_MergeSym],
}


def Extract(tokens):
   env = TokenExtractEnv(tokens, extract_map_root)
   return TokenExtract(env)


if __name__ == "__main__":
   """
   multiple line comments
   """
   import os
   import sys
   from .common import TokenizeText
   filepath = sys.argv[1]
   with open(filepath, 'r') as f:
      code = f.read()
   tokens = Extract(TokenizeText(code))
   print(tokens)
