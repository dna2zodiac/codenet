from .common import Token, TokenType

class TokenScope(object):
   def __init__(self, tokens, data=None):
      self.tokens = tokens
      self.data = data


def _DecorateDefaultFn(env, scope):
   token = env.GetToken(env.i)
   scope.tokens.append(token)
   env.i += 1


class TokenDecorateEnv(object):
   def __init__(self, tokens, decorate_map_root, decorate_default_fn=_DecorateDefaultFn):
      self.i = 0
      self.n = len(tokens)
      self.tokens = tokens
      self.scope_stack = None
      self.decorate_stack = [decorate_map_root]
      self.decorate_default_fn = decorate_default_fn

   def HasNext(self):
      return self.i < self.n

   def GetToken(self, index):
      return self.tokens[index]

   def GetDecorateMap(self):
      return self.decorate_stack[-1]


def TokenDecorate(env, i=0, j=-1):
   if j < 0:
      j = env.n - 1
   scope = TokenScope([], {})
   if env.scope_stack:
      env.scope_stack.append(scope)
   else:
      env.scope_stack = [scope]
   env.i = i
   while env.HasNext() and env.i <= j:
      token = env.GetToken(env.i)
      decorate_map = env.GetDecorateMap()
      matched = False
      if token.N in decorate_map:
         for fn in decorate_map[token.N]:
            ret = fn(env, scope)
            if ret:
               matched = True
      if not matched:
         env.decorate_default_fn(env, scope)
   env.scope_stack.pop()
   return scope
