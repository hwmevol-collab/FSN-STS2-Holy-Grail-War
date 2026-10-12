"""Diagnostic-only calls to unmodified FUC MIPS functions in isolated PPSSPP.

These tests are NOT natural gameplay pose captures. All injected input, outputs,
addresses and source assets are retained. No ISO/EBOOT/catalog file is patched.
"""
from fuc_anim_debugger import *
import struct

class Harness:
    PREFIX=0x08801000
    RETURN=0x08801000
    STACK=0x08803f00
    def __init__(self):
        self.d=Debugger();self.d.pause()
        self.before=self.d.call('cpu.getAllRegs')
        self.prefix=self.d.read(self.PREFIX,0x3000)
        if any(self.prefix):raise RuntimeError('Expected unused zero prefix; do not inject')
        # Bound JIT decoding as well as execution; do not let it scan data.
        self.write(self.RETURN,struct.pack('<II',0x1000ffff,0))
        self.d.call('cpu.breakpoint.add',address=self.RETURN,enabled=True)
        jsonwrite(AW/'Runtime/DIAGNOSTIC_HARNESS.json',dict(purpose='diagnostic_only function-level tests; not naturally loaded character poses',scratch=[hex(self.PREFIX),hex(self.PREFIX+0x3000)],cpu_before=self.before,original_prefix_sha256=hashlib.sha256(self.prefix).hexdigest(),elf_unchanged=True))
    def write(self,a,b):
        self.d.call('memory.write',address=a,base64=base64.b64encode(b).decode())
    def reg(self,name,value):self.d.call('cpu.setReg',name=name,value=value)
    def call(self,fn,**regs):
        for k,v in dict(sp=self.STACK,ra=self.RETURN,**regs).items():self.reg(k,v)
        self.reg('pc',fn);self.d.resume()
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            s=self.d.call('cpu.status')
            if s.get('stepping'):
                if s['pc']!=self.RETURN:raise RuntimeError(('Unexpected stop',s))
                return self.d.call('cpu.getReg',name='v0')['uintValue']
            time.sleep(.005)
        self.d.pause();raise TimeoutError(hex(fn))
    def close(self):
        self.d.pause();self.write(self.PREFIX,self.prefix)
        self.d.call('cpu.breakpoint.remove',address=self.RETURN)
        for c in self.before['categories']:
            for n,v in zip(c['registerNames'],c['uintValues']):
                if n!='pc':self.reg(n,v)
        self.reg('pc',self.before['categories'][0]['uintValues'][32])
        # Discard any diagnostic heap allocations and FPU control-state effects.
        self.d.call('game.reset',**{'break':True});self.d.close()

def run():
    import numpy as np,bisect
    idx=readjson(EU/'Metadata/ANIMATION_INDEX.json');h=Harness();results=[]
    try:
        for code in ['sir','rin','lan']:
            clips=[r for r in idx if r['source_name']==f'chr/{code}/0000.mot' and r['working_path']]
            r=next(x for x in clips if any(c['key_count']>3 for c in readjson(x['working_path'])['channels'] if c['values']))
            j=readjson(r['working_path']);channels=[c for c in j['channels'] if c['key_count']>1 and c['values']][:12]
            for c in channels:
                vals=np.asarray(c['values'],dtype=np.float32);times=np.asarray(c['times'],dtype=np.float32)
                # Reproduce the game's relocated, byte-swapped channel pointers.
                hdr=bytearray(32);struct.pack_into('<I',hdr,0,(c['flags']<<16)|c['track_flags']);struct.pack_into('<HH',hdr,4,c['source_bone_id'],c['key_count'])
                struct.pack_into('<II',hdr,16,0x08801800,0x08802000)
                h.write(0x08801400,hdr);h.write(0x08801800,times.tobytes())
                packed=b''.join(struct.pack('<4H',*[struct.unpack('>I',struct.pack('>f',float(x)))[0]>>16 for x in v]) for v in vals)
                if len(packed)>0x1400:raise RuntimeError('Diagnostic prefix capacity')
                h.write(0x08802000,packed)
                for fraction in [0,.25,.5,.75,1]:
                    # Probe interior of real segments, including both endpoints.
                    k=min(len(times)-2,max(0,(len(times)-2)//2));t=np.float32(times[k]+np.float32(fraction)*np.float32(times[k+1]-times[k]))
                    if times[k+1]==times[k]:continue
                    h.call(0x08884a30,a0=0x08801200,a1=0x08801400,a2=k,f12=struct.unpack('<I',struct.pack('<f',t))[0])
                    actual=np.asarray(struct.unpack('<4f',h.d.read(0x08801200,16)),dtype=np.float32)
                    alpha=np.float32(np.float32(t-times[k])/np.float32(times[k+1]-times[k]))
                    expected=vals[k]+alpha*(vals[k+1]-vals[k]);err=float(np.max(np.abs(actual-expected)))
                    results.append(dict(mot_asset_id=r['parent_asset_id'],animation_asset_id=r['asset_id'],mot_file=r['source_name'],clip_index=r['motion_table_index'],channel=c['channel_index'],bone_id=c['source_bone_id'],track=hex(c['track_flags']),segment=k,time=float(t),fraction=fraction,runtime_values=json.dumps(actual.tolist()),offline_values=json.dumps(expected.tolist()),max_abs_error=err,status='PASS' if err<=1e-6 else 'FAIL',evidence_address='0x08884A30',evidence_scope='diagnostic_only unmodified function with injected relocated real channel data; not character pose'))
        csvwrite(AW/'Runtime/FUC_RUNTIME_CHANNEL_COMPARISON.csv',results)
        jsonwrite(AW/'Runtime/CHANNEL_COMPARISON_SUMMARY.json',dict(samples=len(results),passed=sum(x['status']=='PASS' for x in results),max_abs_error=max(x['max_abs_error'] for x in results),function='0x08884A30',scope='diagnostic_only interpolation primitive',model_pose_comparisons=0,source_codes=['sir','rin','lan']))
        log('CHANNEL TEST',readjson(AW/'Runtime/CHANNEL_COMPARISON_SUMMARY.json'))
    finally:h.close()
if __name__=='__main__':run()
