from fuc_general_debugger import *
import argparse,time
p=argparse.ArgumentParser();p.add_argument('buttons',nargs='*');p.add_argument('--hold',type=float,default=.15);p.add_argument('--settle',type=float,default=.35);a=p.parse_args();d=BattleDebugger()
try:
 for button in a.buttons:
  d.pause();d.call('input.buttons.send',buttons={button:True});d.resume();time.sleep(a.hold);d.pause();d.call('input.buttons.send',buttons={button:False});d.resume();time.sleep(a.settle)
 if not a.buttons:d.resume();time.sleep(a.settle)
 d.pause()
finally:d.close()
