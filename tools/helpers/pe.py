import struct,sys
import os; D=open(os.environ.get('EXE','Furnica.exe'),'rb').read()
pe=struct.unpack_from('<I',D,0x3c)[0]
ns=struct.unpack_from('<H',D,pe+6)[0]; osz=struct.unpack_from('<H',D,pe+20)[0]
IB=struct.unpack_from('<I',D,pe+24+28)[0]
secs=[]
o=pe+24+osz
for i in range(ns):
    n=D[o:o+8].rstrip(b'\0').decode(); vs,va,rs,ra=struct.unpack_from('<IIII',D,o+8); secs.append((n,IB+va,vs,ra,rs)); o+=40
def off(v):
    for n,va,vs,ra,rs in secs:
        if va<=v<va+max(vs,rs): return v-va+ra
def rd(v,n): o=off(v); return D[o:o+n]
def u32(v): return struct.unpack('<I',rd(v,4))[0]
def lstr(v):
    l=u32(v-4); return rd(v,l).decode('cp1250','replace')
if __name__=='__main__':
    for s in secs: print(s[0],hex(s[1]),hex(s[2]),hex(s[3]),hex(s[4]))
