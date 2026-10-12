"""Clear only this research instance's diagnostic breakpoints and release game buttons."""
from fuc_battle_debugger import *
def main():
 d=BattleDebugger()
 try:
  d.pause();before=dict(cpu=d.call('cpu.breakpoint.list'),memory=d.call('memory.breakpoint.list'))
  for p in before['cpu'].get('breakpoints',[]):d.call('cpu.breakpoint.remove',address=p['address'])
  for p in before['memory'].get('breakpoints',[]):d.call('memory.breakpoint.remove',address=p['address'],size=p['size'])
  jsonwrite(BR/'DEBUGGER_CLEANUP_BEFORE_BUTTONS.json',dict(timestamp=now(),before=before,bps_cleared=True))
  d.call('input.buttons.send',buttons={x:False for x in ['up','down','left','right','cross','circle','square','triangle','start','select']})
  after=dict(cpu=d.call('cpu.breakpoint.list'),memory=d.call('memory.breakpoint.list'));assert not after['cpu'].get('breakpoints') and not after['memory'].get('breakpoints')
  jsonwrite(BR/'DEBUGGER_CLEANUP.json',dict(timestamp=now(),before=before,after=after,hooks_written=0,game_ram_patch_used=False,diagnostic_eboot_used=False));print('breakpoints cleared; no RAM hooks installed')
 finally:d.close()
if __name__=='__main__':main()
