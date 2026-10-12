from fuc_semantic_common import *
import argparse
def payload(name):
    rows=[r for r in readrows(EU/'Metadata/FPK_EXTRACTED_INDEX.csv') if r['name']==name]
    assert rows and len({r['sha256'] for r in rows})==1
    return rows[0],pathlib.Path(rows[0]['physical_path']).read_bytes()
def main():
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--start',type=lambda x:int(x,0),default=0);p.add_argument('--end',type=lambda x:int(x,0),default=256);p.add_argument('--strings',action='store_true');a=p.parse_args()
    r,b=payload(a.name);print(a.name,'bytes',len(b),'sha',r['sha256']);print('HEADER',b[:64].hex())
    if a.strings:
        vals=[dict(offset=m.start(),text=m[0].decode('ascii')) for m in re.finditer(rb'[\x20-\x7e]{5,}',b)]
        out=SW/'Static'/('strings_'+a.name.replace('/','_')+'.json');jsonwrite(out,vals)
        for v in vals[:90]:print(hex(v['offset']),repr(v['text']))
        print('TOTAL',len(vals))
    else:
        for o in range(a.start,min(a.end,len(b)-15),16):print(hex(o),' '.join(f'{x:08x}' for x in struct.unpack_from('<4I',b,o)))
if __name__=='__main__':main()
