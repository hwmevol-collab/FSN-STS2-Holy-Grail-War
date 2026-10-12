from fuc_anim_glb_export import *
def main():
    bi=readrows(EU/'Metadata/SOURCE_BONE_INDEX.csv');idx=readjson(EU/'Metadata/ANIMATION_INDEX.json')
    for r in readjson(AW/'GLB_EXPORTS.json'):
        code=r['mot_file'].split('/')[1];mi=next(m for m in readrows(EU/'Metadata/MODEL_INDEX.csv') if m['asset_id']==r['model_asset_id']);mapping={int(b['source_bone_ordinal']):int(b['glb_node_id']) for b in bi if b['model_sha256']==mi['source_sha256']};g,b=load_glb(r['animated_glb']);a=g['accessors'][g['animations'][0]['samplers'][0]['input']];v=g['bufferViews'][a['bufferView']];times=np.frombuffer(b,dtype='<f4',count=a['count'],offset=v.get('byteOffset',0)+a.get('byteOffset',0));ir=next(i for i in idx if i['asset_id']==r['animation_asset_id']);decoded=readjson(ir['working_path']);sk=skeleton(code);lut=np.frombuffer((AW/f'Runtime/Motion/{code}/rotation_sine_lut.bin').read_bytes(),dtype='<f4');frames=[]
        for t in times:
            p=evaluate(decoded,sk,t,lut);frames.append(dict(time=float(t),nodes=[dict(glb_node=mapping[n['ordinal']],ordinal=n['ordinal'],world_matrix=n['world_matrix']) for n in p['nodes']]))
        out=pathlib.Path(r['animated_glb']).parent/'viewer'/(pathlib.Path(r['animated_glb']).stem+'.reference.json');jsonwrite(out,dict(animation_asset_id=r['animation_asset_id'],scope='source evaluator already cross-checked with original runtime; independent viewer must match all baked frame world matrices',tolerance=2e-4,frames=frames));log('VIEWER REFERENCE',out.name,len(frames))
if __name__=='__main__':main()
