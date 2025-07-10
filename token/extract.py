from .common import Token, TokenType, IsSym

def _ExtractDefaultFn(env, out):
   token = env.GetToken(env.i)
   if token == '\n':
      env.L += 1
      env.C = 0
   else:
      t = Token(token, TokenType.SYM, env.L, env.C)
      env.C = len(token)
      out.append(t)
   env.i += 1

class TokenExtractEnv(object):
   def __init__(self, tokens, extract_map_root, extract_default_fn=_ExtractDefaultFn):
      self.L = 0
      self.C = 0
      self.i = 0
      self.n = len(tokens)
      self.tokens = tokens
      self.extract_stack = [extract_map_root]
      self.extract_default_fn = extract_default_fn

   def HasNext(self):
      return self.i < self.n

   def GetToken(self, index):
      return self.tokens[index]

   def GetExtractMap(self):
      return self.extract_stack[-1]


def TokenExtract(env):
   env.L = 0
   env.C = 0
   out = []
   while env.HasNext():
      token = env.GetToken(env.i)
      extract_map = env.GetExtractMap()
      matched = False
      if token in extract_map:
         for fn in extract_map[token]:
            ret = fn(env, out)
            if ret:
               matched = True
               break
      if not matched:
         env.extract_default_fn(env, out)
   return out


def ExtractQuote(env, out):
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


def MarkLineNumber(env, out):
   t = Token("\n", TokenType.BR, env.L, env.C)
   out.append(t)
   env.i += 1
   env.L += 1
   env.C = 0
   return True

def MergeSymUnderline(env, out):
   L = env.L
   C = env.C
   if env.i != 0 and out[-1].T == TokenType.SYM and (out[-1].N == '_' or IsSym(out[-1].N)):
      t = out[-1]
      t.N += '_'
   else:
      t = Token('_', TokenType.SYM, L, C)
      out.append(t)
   C += 1
   if env.i+1 < env.n:
      token = env.GetToken(env.i+1)
      if IsSym(token):
         t.N += token
         C += len(token)
         env.i += 1
   env.i += 1
   env.C = C
   return True

