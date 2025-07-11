def a():
   print\
("hello")
   if (True and
False):
      print("1")

def b(fn):
   return 0

def b2(i):
   def wrap(fn):
      return fn
   return wrap

@b
@b2(2)
def c():
   return 1


if 1:  \
# comment
   print(2)


if 1:
   if 1:
      if 1:
         if 1:
            print(111)

print(123 if 1 else 0)
print([x+1 for x in [1,2,3]])

a\
    ()
