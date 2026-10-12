from pathlib import Path
import shutil, os, json, configparser, hashlib, secrets
ROOT=Path('E:/FSN_Trailer')
PROJECT=Path('E:/BaiduNetdiskDownload/FSN/milestone-a')
base=PROJECT/'reports/workshop-beta-performance-v0.9.4-20261012-01/runtime-playtest'
rt=ROOT/'runtime/game'
rt.mkdir(parents=True,exist_ok=True)
# Only immutable game binaries are linked; every mod/config/save is copied.
for p in base.iterdir():
    if p.is_file() and p.suffix.lower() in ('.exe','.dll','.pck'):
        dest=rt/p.name
        if not dest.exists(): os.link(p,dest)
for dirname in ['data_sts2_windows_x86_64','mods']:
    shutil.copytree(base/dirname,rt/dirname,dirs_exist_ok=True)
payload=Path('E:/SteamLibrary/steamapps/workshop/content/2868840/3818087982')
shutil.copytree(payload,rt/'mods/RinArcherCore',dirs_exist_ok=True)
assert hashlib.sha256((rt/'mods/RinArcherCore/RinArcherCore.dll').read_bytes()).hexdigest().upper()=='EA6D633441A3E1842EF8ACBF89CEB03CA99C5D673DD60AB4D9CDAECBC4DFE6F7'
(rt/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="E:/FSN_Trailer/saves"\n[debug]\nfile_logging/log_path="E:/FSN_Trailer/temp/game.log"\n[sentry]\nconfig/dsn=""\nconfig/enabled=false\n',encoding='utf-8')
cfg=ROOT/'runtime/config/obs-studio'
(cfg/'basic/profiles/FSN').mkdir(parents=True,exist_ok=True)
(cfg/'basic/scenes').mkdir(parents=True,exist_ok=True)
(cfg/'plugin_config/obs-websocket').mkdir(parents=True,exist_ok=True)
ini=configparser.ConfigParser(interpolation=None);ini.optionxform=str
ini.read(Path(os.environ['APPDATA'])/'obs-studio/basic/profiles/A/basic.ini',encoding='utf-8-sig')
ini['General']['Name']='FSN Trailer'
ini['AdvOut']['RecFilePath']='E:/FSN_Trailer/raw'
ini['AdvOut']['RecTracks']='1'
ini['AdvOut']['RecRB']='false'
ini['AdvOut']['RecFormat2']='mkv'
ini['AdvOut']['RecEncoder']='obs_nvenc_h264_tex'
ini['Output']['FilenameFormatting']='FSN_%CCYY-%MM-%DD_%hh-%mm-%ss'
with (cfg/'basic/profiles/FSN/basic.ini').open('w',encoding='utf-8') as f:ini.write(f,space_around_delimiters=False)
orig=Path(os.environ['APPDATA'])/'obs-studio/basic/profiles/A/recordEncoder.json'
if orig.exists():shutil.copy2(orig,cfg/'basic/profiles/FSN/recordEncoder.json')
(cfg/'global.ini').write_text('[General]\nFirstRun=false\n[Basic]\nProfile=FSN Trailer\nProfileDir=FSN\nSceneCollection=FSN Trailer\nSceneCollectionFile=FSN\n[BasicWindow]\nPreviewEnabled=true\n',encoding='utf-8')
(cfg/'user.ini').write_text('[General]\nFirstRun=false\nHotkeyFocusType=NeverDisableHotkeys\n[Basic]\nProfile=FSN Trailer\nProfileDir=FSN\nSceneCollection=FSN Trailer\nSceneCollectionFile=FSN\nConfigOnNewProfile=false\n[BasicWindow]\nPreviewEnabled=true\n',encoding='utf-8')
(cfg/'basic/scenes/FSN.json').write_text(json.dumps({'name':'FSN Trailer','current_scene':'FSN Trailer','current_program_scene':'FSN Trailer','scene_order':[{'name':'FSN Trailer'}],'sources':[{'name':'FSN Trailer','id':'scene','versioned_id':'scene','settings':{'items':[]}}]},ensure_ascii=False),encoding='utf-8')
(cfg/'plugin_config/obs-websocket/config.json').write_text(json.dumps({'server_enabled':True,'server_port':4456,'auth_required':True,'server_password':secrets.token_urlsafe(32),'alerts_enabled':False}),encoding='utf-8')
(ROOT/'temp/portable_mode.txt').write_text('Independent OBS portable configuration; original OBS untouched.',encoding='utf-8')
print('Prepared isolated v0.9.4 game and OBS configuration')
