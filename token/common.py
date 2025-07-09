import string
from enum import Enum


class TokenType(Enum):
   SYM   = 0
   MOD   = 1
   KLASS = 2
   FUNC  = 3
   VAR   = 4
   CONST = 5
   UNK   = 9


class TokenLang(Enum):
   NONE   = 0
   CPP    = 1
   PYTHON = 2


class Token(object):
   def __init__(self, N, T, L, C, lang=None, langver=None, data=None):
      self.N = N # name
      self.T = T # type
      self.L = L # line number
      self.C = C # line column
      self.lang = lang
      self.langver = langver
      self.data = data

   def __repr__(self):
      return f'({self.N},{self.T},{self.L}-#{self.C})'


def TokenizeText(text):
   """
   Parse text into tokens: punctuation, whitespace, and word characters.

   Args:
      text (str): Input text to tokenize

   Returns:
      list: List of tokens
   """
   tokens = []
   current_token = ""

   for char in text:
      if char in string.punctuation:
         # If we have accumulated word characters, add them as a token
         if current_token:
            tokens.append(current_token)
            current_token = ""
         # Add punctuation as separate token
         tokens.append(char)
      elif char.isspace():
         # If we have accumulated word characters, add them as a token
         if current_token:
            tokens.append(current_token)
            current_token = ""
         # Add whitespace as separate token
         tokens.append(char)
      else:
         # Accumulate word characters
         current_token += char

   # Don't forget the last token if text doesn't end with punctuation/space
   if current_token:
      tokens.append(current_token)

   return tokens


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


def FindNext(env, token0, start_index=0):
   for i in range(start_index, env.n):
      if env.GetToken(i) == token0:
         return i
   return -1


def FindPrev(env, token0, start_index):
   for i in range(start_index-1, -1, -1):
      if env.GetToken(i) == token0:
         return i
   return -1


if __name__ == "__main__":
   # Test with your example
   import sys
   if len(sys.argv) > 1:
      with open(sys.argv[1], 'r') as f:
         text = f.read()
   else:
      text = "hello world! we have\ta test\n\n"
   result = TokenizeText(text)
   print(result)
