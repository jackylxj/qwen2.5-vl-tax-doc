import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGET = {'发票号码': '00123', '开票日期': '2025年01月02日',
          '购买方名称': '测试公司', '购买方税号': None, '价税合计（小写）': '￥123.00'}


class ScoreTests(unittest.TestCase):
    def score(self, fields, target=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'pred').mkdir()
            (root / 'gold.json').write_text(json.dumps({'docs': [
                {'id': 'fixture', 'target': TARGET if target is None else target}]}), encoding='utf-8')
            (root / 'pred/fixture.json').write_text(json.dumps({'fields': fields}), encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/score.py'),
                                     str(root / 'gold.json'), str(root / 'pred')],
                                    check=True, capture_output=True, text=True)
            return json.loads(result.stdout)

    def test_date_and_amount_normalization(self):
        fields = {**TARGET, '开票日期': '2025-1-2', '价税合计（小写）': '123'}
        self.assertEqual(self.score(fields), {'correct': 5, 'total': 5, 'whole': 1, 'complete': 1})

    def test_missing_null_field_is_wrong(self):
        fields = dict(TARGET); del fields['购买方税号']
        self.assertEqual(self.score(fields)['correct'], 4)

    def test_leading_zero_loss_is_wrong(self):
        self.assertEqual(self.score({**TARGET, '发票号码': '123'})['correct'], 4)

    def test_extra_field_fails_whole_document(self):
        self.assertEqual(self.score({**TARGET, 'extra': 'x'})['whole'], 0)

    def test_partial_labels_are_not_complete_documents(self):
        self.assertEqual(self.score(TARGET, {'发票号码': '00123'}),
                         {'correct': 1, 'total': 1, 'whole': 0, 'complete': 0})


if __name__ == '__main__':
    unittest.main()
