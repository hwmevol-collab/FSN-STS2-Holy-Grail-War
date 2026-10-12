"""Offline x86 CXDEC reference execution in Unicorn; no OS or game execution.
Only the verified internal key generator executes. It has no file/network API.
The recovered TPM supplies code; each archive supplies its matching control block.
"""
from common import *
from fha_prepare import ROOT,FHA,FW
import pefile,unicorn,zlib
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX
class Filter:
    def __init__(self,control_tpm=None):
        p=FHA/'RawExtracted/Molebox/FateFD.exe/default/cxdec.tpm';pe=pefile.PE(str(p));self.u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_32)
        self.u.mem_map(0x10000000,(pe.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);self.u.mem_write(0x10000000,pe.get_memory_mapped_image())
        self.u.mem_map(0x20000000,0x20000);self.u.mem_map(0x30000000,0x100000)
        self.u.mem_write(0x300e0000,bytes.fromhex('b8ffffffffc3'));self.u.mem_write(0x300e0010,bytes.fromhex('b801000000c20c00'))
        self.u.mem_write(0x10007000,struct.pack('<II',0x300e0000,0x300e0010))
        # Skip OS allocator. These are verified globals in this specific recovered TPM.
        self.u.mem_write(0x1000c8a0,struct.pack('<I',0x30000000));self.u.mem_write(0x1000caa8,b'\xff'*400);self.u.mem_write(0x1000cc38,struct.pack('<I',1))
        if control_tpm:
            b=pathlib.Path(control_tpm).read_bytes();pos=b.find(b' Encryption control block');assert pos>=0
            self.u.mem_write(0x10008fd8,b[pos:pos+4096])
        self.cache={}
    def derive(self,key):
        if key not in self.cache:
            self.u.mem_write(0x20010000,struct.pack('<III',0x300f0000,0x20000000,0x20000004));self.u.reg_write(UC_X86_REG_ESP,0x20010000);self.u.reg_write(UC_X86_REG_EAX,key)
            self.u.emu_start(0x10001450,0x300f0000,count=1000000)
            self.cache[key]=struct.unpack('<II',self.u.mem_read(0x20000000,8))
        return self.cache[key]
    def decrypt(self,raw,key):
        b=bytearray(raw);boundary=min(len(b),(key&0x143)+0x787)
        for lo,hi,k in [(0,boundary,key),(boundary,len(b),(key>>16)^key)]:
            r0,r1=self.derive(k);p0=r1>>16;p1=r1&65535
            if p0==p1:p1+=1
            if lo<=p0<hi:b[p0]^=(r0>>8)&255
            if lo<=p1<hi:b[p1]^=(r0>>16)&255
            x=(r0&255) or 1;b[lo:hi]=b[lo:hi].translate(bytes(v^x for v in range(256)))
        return bytes(b)

def repair():
    from fha_extract import payload
    from verify_xp3 import index
    p=next(ROOT.rglob('sound.xp3'));es=index(p);filt=Filter(next(ROOT.rglob('cxdec.tpm')));repairs=[]
    for e in es:
        if e['source_logical_path'] not in ('se245.wav','se247.wav'):continue
        raw=payload(p,e);b=filt.decrypt(raw,e['adler32']);actual=zlib.adler32(b);print(e['source_logical_path'],hex(actual),hex(e['adler32']),filt.derive((e['adler32']>>16)^e['adler32']),flush=True)
        dst=FHA/'RawExtracted/XP3/sound.xp3'/e['source_logical_path'];before=sha(dst)
        if actual==e['adler32']:
            dst.write_bytes(b);repairs.append(dict(path=str(dst),before_sha256=before,sha256=sha(dst),adler32=actual,method='Recovered TPM XCode generator; native equal-offset correction; verified Adler32'))
        else:
            assert dst.read_bytes()==b
            repairs.append(dict(path=str(dst),sha256=before,adler32=actual,expected_adler32=e['adler32'],status='CHECKSUM_EXCEPTION_REFERENCE_DECODER_IDENTICAL',method='Independent recovered TPM XCode generator yields identical bytes; original checksums remain unmatched'))
    rows=[json.loads(s) for s in (FHA/'Metadata/RAW_ASSETS.jsonl').open(encoding='utf-8')];by={r['path']:r for r in repairs}
    for r in rows:
        if r['extracted_path'] in by:
            evidence=by[r['extracted_path']];r.update(sha256=evidence['sha256'],adler32_verified='status' not in evidence,decrypt_method='CXDEC FHA; independently checked against recovered TPM generator')
    with (FHA/'Metadata/RAW_ASSETS.jsonl').open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    logs=json.loads((FHA/'Metadata/EXTRACTION_LOG.json').read_text('utf-8'))
    for log in logs:
        if pathlib.Path(log['source_container']).name=='sound.xp3':log['reference_filter_evidence']=repairs
    jsonwrite(FHA/'Metadata/EXTRACTION_LOG.json',logs);jsonwrite(FHA/'Metadata/CXDEC_REFERENCE_REPAIRS.json',repairs)
if __name__=='__main__':repair()
