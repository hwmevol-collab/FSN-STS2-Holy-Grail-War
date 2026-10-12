from pathlib import Path
import shutil,hashlib,json
O=Path(__file__).resolve().parent;B=Path('E:/BaiduNetdiskDownload/FSN/milestone-a/reports/game-v0111-compat-20261013-01')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
identities=[dict(GameVersion='v0.107.1',Commit='59260271',AssemblySha256='A1F9E653F1E28E4076558FEE1E60D218619CB7E057B887C6417F62C62C6D7A52',AssemblyMvid='97f10687-c306-4798-ab75-8b9f23f34dfb'),dict(GameVersion='v0.111.0',Commit='41cef1ea',AssemblySha256='0861BFA1DF347538D932F22D580E75420F08082792EB914E53B4882764ACDBE9',AssemblyMvid='73b63ee0-6c0a-47bb-b0d1-b21f6d94222e')]
for api in ['107','111']:
 p=O/('package-'+api)
 if not p.exists():shutil.copytree(B/'package-111',p)
 shutil.copy2(O/('build/candidate-'+api)/'RinArcherCore.dll',p/'mods/RinArcherCore/RinArcherCore.dll')
dual=O/'package-dual'
if not dual.exists():shutil.copytree(B/'package-111',dual)
mod=dual/'mods/RinArcherCore';variants=[]
for api,identity in zip(['107','111'],identities):
 d=mod/'lib'/identity['GameVersion'][1:];d.mkdir(parents=True,exist_ok=True)
 shutil.copy2(O/('build/candidate-'+api)/'RinArcherCore.dll',d/'RinArcherCore.dll')
 variants.append(dict(Game=identity,Directory='lib/'+identity['GameVersion'][1:],PayloadSha256=sha(d/'RinArcherCore.dll')))
shutil.copy2(O/'build/loader/bin/Release/net9.0/RinArcherCore.Loader.dll',mod/'RinArcherCore.dll')
(mod/'mod-variants.manifest').write_text(json.dumps(dict(Schema=1,Variants=variants),indent=2),'utf-8')
shutil.copy2(O/'build/loader/STS2-Template.LICENSE',mod/'STS2-Template.LICENSE')
(mod/'THIRD_PARTY_NOTICES.txt').write_text('Native content assembly registration and initializer forwarding adapted from SlayTheCircle/STS2-Template, MIT, copyright (c) 2026 3aKHP.\nPinned source: https://github.com/SlayTheCircle/STS2-Template/tree/767e7be8c1f7d7a0d51e261e1147023d852ab881/src/STS2-Template.Loader\nIts loader was derived from STS2-RitsuLib (MIT, OLC). FSN uses exact game build identities and refuses unknown builds.\n','utf-8')
print(json.dumps(dict(variants=variants,loader=sha(mod/'RinArcherCore.dll'))))
