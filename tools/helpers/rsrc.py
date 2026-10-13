from pe import *
RVA=0x46b000; base=off(RVA)
def walk(o,lvl,path):
    nn,ni=struct.unpack_from('<HH',D,base+o+12)
    for k in range(nn+ni):
        nm,ofs=struct.unpack_from('<II',D,base+o+16+8*k)
        if nm&0x80000000:
            p=base+(nm&0x7fffffff); l=struct.unpack_from('<H',D,p)[0]; name=D[p+2:p+2+2*l].decode('utf-16le')
        else: name=nm
        if ofs&0x80000000: yield from walk(ofs&0x7fffffff,lvl+1,path+[name])
        else:
            rva,sz=struct.unpack_from('<II',D,base+ofs); yield path+[name],RVA+rva-0x46b000+0x46b000 if False else rva+0x400000,sz
for p,va,sz in walk(0,0,[]): print(p,hex(va),sz)
