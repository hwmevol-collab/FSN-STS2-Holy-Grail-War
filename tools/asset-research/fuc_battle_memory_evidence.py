"""Save small named memory regions from a paused isolated runtime into WORK."""
from fuc_battle_debugger import *
import argparse
def main():
 p=argparse.ArgumentParser();p.add_argument('address',type=lambda x:int(x,0));p.add_argument('size',type=lambda x:int(x,0));p.add_argument('path');a=p.parse_args();d=BattleDebugger()
 try:d.pause();d.dump(a.address,a.size,BR/a.path);print(BR/a.path)
 finally:d.close()
if __name__=='__main__':main()
