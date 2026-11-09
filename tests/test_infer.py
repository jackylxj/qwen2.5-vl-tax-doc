import json
import unittest
from unittest.mock import Mock, patch

from app.infer import infer


def envelope(content='{}', **kwargs):
    return {'model': 'vat-base', 'choices': [{'message': {'content': content}, 'finish_reason': 'stop'}], **kwargs}


class InferenceTests(unittest.TestCase):
    def setUp(self):
        self.post = self.enterContext(patch('app.infer.httpx.post'))
        self.response = Mock()
        self.post.return_value = self.response

    def test_json_and_fenced_json(self):
        for content in ['{"x":null}', '```json\n{"x":null}\n```', '```\n{"x":null}\n```']:
            self.response.json.return_value = envelope(content)
            self.assertEqual(infer(b'jpeg', 'prompt', 'vat-base')['parsed'], {'x': None})

    def test_request_contains_image_and_ocr(self):
        self.response.json.return_value = envelope()
        infer(b'jpeg', 'prompt', 'vat-base', ['OCR文字'])
        body = self.post.call_args.kwargs['json']
        content = body['messages'][0]['content']
        self.assertTrue(content[0]['image_url']['url'].startswith('data:image/jpeg;base64,'))
        self.assertIn('OCR文字', content[1]['text'])
        self.assertEqual(body['temperature'], 0)

    def test_invalid_envelopes_are_rejected(self):
        cases = [[], {}, envelope(model='wrong'), {'model': 'vat-base', 'choices': []},
                 envelope(None), envelope(''), envelope('not json')]
        truncated = envelope(); truncated['choices'][0]['finish_reason'] = 'length'; cases.append(truncated)
        for data in cases:
            with self.subTest(data=data):
                self.response.json.return_value = data
                with self.assertRaises(ValueError):
                    infer(b'jpeg', 'prompt', 'vat-base')

    def test_duplicate_json_keys_are_rejected(self):
        self.response.json.return_value = envelope('{"tax":null,"tax":"invented"}')
        with self.assertRaises(ValueError):
            infer(b'jpeg', 'prompt', 'vat-base')


if __name__ == '__main__':
    unittest.main()
