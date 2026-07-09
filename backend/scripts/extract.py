import marshal, types, sys
def get_strs(c):
    return [x for x in c.co_consts if isinstance(x, str)] + sum([get_strs(x) for x in c.co_consts if isinstance(x, types.CodeType)], [])

f = open(sys.argv[1], 'rb')
f.read(16)
code = marshal.load(f)
for s in get_strs(code):
    print(s)
