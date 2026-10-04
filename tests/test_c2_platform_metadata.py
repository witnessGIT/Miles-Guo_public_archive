import json
from pathlib import Path
import sys
import unittest
from urllib.request import Request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import c2_platform_metadata as m

class PlatformMetadataTests(unittest.TestCase):
    def test_exact_post_target_only(self):
        self.assertEqual(m.post_id_from_url('https://gettr.com/post/p23qiok5c87'),'p23qiok5c87')
        for url in ['https://evil.test/post/p23qiok5c87','https://gettr.com/post/p23qiok5c87?x=1','https://gettr.com/streaming/p23qiok5c87','https://u:p@gettr.com/post/p23qiok5c87','http://gettr.com/post/p23qiok5c87']:
            with self.subTest(url=url), self.assertRaises(ValueError):m.post_id_from_url(url)
    def test_missing_type_remains_unknown(self):
        raw=json.dumps({'result':{'data':{'_id':'p123456','vid':'private-path-not-fetched','uid':'public-user'}}}).encode()
        value=m.summarize_json(raw,'p123456')
        self.assertIsNone(value['p_type']); self.assertTrue(value['has_vid_field'])
        self.assertNotIn('private-path-not-fetched',str(value)); self.assertNotIn('decision',value)
    def test_stream_type_is_preserved_without_processing(self):
        raw=json.dumps({'result':{'data':{'_id':'p123456','p_type':'stream','_t':'post'}}}).encode()
        self.assertEqual(m.summarize_json(raw,'p123456')['p_type'],'stream')
    def test_wrong_id_rejected(self):
        with self.assertRaises(ValueError):m.summarize_json(b'{"result":{"data":{"_id":"other"}}}','p123456')
    def test_redirect_refused(self):
        with self.assertRaises(ValueError):m.NoRedirect().redirect_request(Request('https://api.gettr.com/u/post/p123456'),None,302,'',{},'https://elsewhere.test')

if __name__=='__main__':unittest.main()
