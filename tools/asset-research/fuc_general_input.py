"""Bounded UI input through the isolated debugger, returning to a paused frame."""
from fuc_general_debugger import *
import argparse,time
def main():
 p=argparse.ArgumentParser();p.add_argument('button',nargs='?',default='');p.add_argument('--frames',type=int,default=3);p.add_argument('--settle',type=float,default=.2);p.add_argument('--repeat',type=int,default=1);a=p.parse_args();d=BattleDebugger()
 try:
  d.pause();d.resume()
  for _ in range(a.repeat):
   if a.button:d.call('input.buttons.press',button=a.button,duration=a.frames)
   time.sleep(a.settle)
  print(d.pause())
 finally:d.close()
if __name__=='__main__':main()
