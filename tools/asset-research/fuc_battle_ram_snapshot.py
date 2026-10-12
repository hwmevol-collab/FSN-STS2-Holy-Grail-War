"""Pause and preserve PSP user RAM for repeatable pointer/table analysis; read-only game memory."""
from fuc_battle_debugger import *
import argparse,base64
def main():
    p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args();out=BR/'Snapshots'/a.name;out.mkdir(parents=True,exist_ok=True);d=BattleDebugger()
    try:
        d.pause();d.dump(0x08800000,0x1800000,out/'user_ram.bin');jsonwrite(out/'REGISTERS.json',regs(d))
        try:
            r=d.call('gpu.buffer.screenshot',type='uri');raw=base64.b64decode(r['uri'].split(',',1)[1]);(out/'runtime.png').write_bytes(raw)
        except Exception as e:jsonwrite(out/'SCREENSHOT_LIMITATION.json',{'error':str(e)})
        print(str(out))
    finally:d.close()
if __name__=='__main__':main()
