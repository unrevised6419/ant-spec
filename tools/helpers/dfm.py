from pe import *
import sys
class R:
    def __init__(s,b): s.b=b; s.p=0
    def u8(s): v=s.b[s.p]; s.p+=1; return v
    def n(s,k): v=s.b[s.p:s.p+k]; s.p+=k; return v
    def ss(s): l=s.u8(); return s.n(l).decode('cp1250')
def val(r):
    t=r.u8()
    if t==0: return None
    if t==1:
        L=[]
        while r.b[r.p]!=0: L.append(val(r))
        r.p+=1; return L
    if t==2: return struct.unpack('<b',r.n(1))[0]
    if t==3: return struct.unpack('<h',r.n(2))[0]
    if t==4: return struct.unpack('<i',r.n(4))[0]
    if t==5: r.n(10); return '<ext>'
    if t in (6,7): return r.ss() if t==6 else ('ident:'+r.ss())
    if t==8: return False
    if t==9: return True
    if t==10: l=struct.unpack('<I',r.n(4))[0]; r.n(l); return '<binary %d>'%l
    if t==11:
        L=[]
        while True:
            x=r.ss()
            if not x: break
            L.append(x)
        return set(L)
    if t==12: l=struct.unpack('<I',r.n(4))[0]; return r.n(l).decode('cp1250')
    if t==13: return 'nil'
    if t==14:
        L=[]
        while r.b[r.p]!=0:
            if r.b[r.p] in (2,3,4): val(r)
            r.u8()  # vaList
            item={}
            while r.b[r.p]!=0:
                k=r.ss(); item[k]=val(r)
            r.p+=1; L.append(item)
        r.p+=1; return L
    if t==15: r.n(4); return '<single>'
    if t==18: l=struct.unpack('<I',r.n(4))[0]; return r.n(2*l).decode('utf-16le')
    if t==19: return struct.unpack('<q',r.n(8))[0]
    raise Exception('type %d at %d'%(t,r.p))
def comp(r,ind):
    if r.b[r.p]&0xf0==0xf0:
        f=r.u8()
        if f&2: val(r)
    cls=r.ss(); nm=r.ss()
    print('  '*ind+'object %s: %s'%(nm,cls))
    while r.b[r.p]!=0:
        k=r.ss(); v=val(r)
        print('  '*ind+'  %s = %r'%(k,v))
    r.p+=1
    while r.b[r.p]!=0: comp(r,ind+1)
    r.p+=1
va,sz=int(sys.argv[1],16),int(sys.argv[2])
b=rd(va,sz); assert b[:4]==b'TPF0'
r=R(b); r.p=4; comp(r,0)
