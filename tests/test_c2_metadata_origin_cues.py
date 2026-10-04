"""Origin clues must be observable without becoming automatic classifications."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    'origin_cues_under_test', Path(__file__).resolve().parents[1] / 'scripts/c2_metadata_evidence.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
URL = 'https://www.gwins.org/cn/milesguo/24197.html'


class OriginCueTests(unittest.TestCase):
    def test_colloquial_recording_and_duration_clues_are_retained(self):
        for text in ['这个小视频就说这些。', '我拿手机拍一段。', '这段視頻是補充。',
                     '这次录制到这里。', '还有10分钟开会。', '这是十分鐘的更新。']:
            with self.subTest(text=text):
                result = m.parse_page(('<title>20230103_1</title><p>' + text + '</p>').encode(), URL, '20230103_1')
                self.assertTrue(any(text == item['excerpt'] for item in result['identity_type_cues']))
                self.assertNotIn('decision', result)
                self.assertEqual(result['cue_profile'], 'origin-context-v2')

    def test_other_video_reference_does_not_become_a_decision(self):
        result = m.parse_page('<p>昨天别人的视频是录播，明天我直播。</p>'.encode(), URL, '')
        self.assertTrue(result['identity_type_cues'])
        self.assertNotIn('decision', result)
        self.assertIn('other recordings', result['cue_warning'])

    def test_damaged_excerpts_are_excluded(self):
        raw = '<p>这个小视频'.encode() + b'\xff' + '有坏字。</p><p>这段视频文字正常。</p>'.encode()
        result = m.parse_page(raw, URL, '')
        self.assertFalse(result['decoding']['strict'])
        self.assertTrue(all('\ufffd' not in c['excerpt'] for c in result['identity_type_cues']))
        self.assertFalse(any('坏字' in c['excerpt'] for c in result['identity_type_cues']))

    def test_count_limit_and_hidden_text_remain_enforced(self):
        raw = '<script>隐藏小视频</script><style>隐藏录制</style>'
        raw += ''.join(f'<p>第{i}段视频线索。</p>' for i in range(80))
        result = m.parse_page(raw.encode(), URL, '')
        self.assertEqual(len(result['identity_type_cues']), 40)
        self.assertNotIn('隐藏', str(result))

    def test_no_clue_is_not_negative_evidence(self):
        result = m.parse_page('<p>今天问候大家。</p>'.encode(), URL, '')
        self.assertEqual(result['identity_type_cues'], [])
        self.assertIn('not absence evidence', result['decoding']['warning'])
        self.assertNotIn('decision', result)


if __name__ == '__main__':
    unittest.main()
