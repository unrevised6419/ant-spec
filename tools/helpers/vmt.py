from pe import *
co=off(0x401000)
res={}
for o in range(co, co+0x5a9cc-4, 4):
    v=0x401000+o-co
    p=struct.unpack_from('<I',D,o)[0]
    if p==v+0x4c:
        vmt=p
        nm=u32(vmt-0x2c)
        try:
            l=rd(nm,1)[0]; name=rd(nm+1,l).decode()
        except: continue
        res[name]=vmt
import sys
for n in sys.argv[1:]:
    vmt=res[n]; print(n,hex(vmt))
    ft=u32(vmt-0x38)
    if ft:
        cnt=struct.unpack('<H',rd(ft,2))[0]; ct=u32(ft+2)
        p=ft+6
        for i in range(cnt):
            fo=u32(p); idx=struct.unpack('<H',rd(p+4,2))[0]; l=rd(p+6,1)[0]; fn=rd(p+7,l).decode()
            print('  field +0x%x [idx 0x%x] %s'%(fo,fo//4,fn)); p+=7+l
    mt=u32(vmt-0x34)
    if mt:
        cnt=struct.unpack('<H',rd(mt,2))[0]; p=mt+2
        for i in range(cnt):
            sz=struct.unpack('<H',rd(p,2))[0]; a=u32(p+2); l=rd(p+6,1)[0]; fn=rd(p+7,l).decode()
            print('  method %s @%x'%(fn,a)); p+=sz
