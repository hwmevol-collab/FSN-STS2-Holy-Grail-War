"""Purpose-built debugger operations, with all journal output in this task's WORK layer."""
from fuc_general_debugger import *
import argparse
def main():
    p=argparse.ArgumentParser();p.add_argument('event');p.add_argument('--params',default='{}');a=p.parse_args();d=BattleDebugger()
    try:
        if a.event=='pause':r=d.pause()
        elif a.event=='resume':d.resume();r={'resumed':True}
        else:r=d.call(a.event,**json.loads(a.params))
        print(json.dumps(r,ensure_ascii=False))
    finally:d.close()
if __name__=='__main__':main()
