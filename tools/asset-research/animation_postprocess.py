from animation_common import *

def postprocess():
    log('Waiting for all pinned media checkpoints')
    while True:
        status=read(M/'ANIMATION_STAGE_STATUS.json')
        if status['completed']==status['total']:break
        time.sleep(5)
    assert all(s['status']=='success' for s in status['status']),'Resolve processing failures before final indexing'
    from animation_index import index,duplicates
    from animation_validation import validate
    from animation_qa import qa
    from animation_finalize import verify
    from animation_overviews import overviews
    shutil.copy2(W/'scripts/animation_browser.html',A/'index.html')
    index();overviews();duplicates();validate();qa();verify()
    save(M/'ANIMATION_POSTPROCESS_READY.json',{'created_at':now(),'status':'ready_for_final_visual_and_browser_review','manual_checks_pending':True,'main_catalog_still_frozen':True})
    log('Full indexes ready for final review')

if __name__=='__main__':postprocess()
