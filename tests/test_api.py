import base64
import io
import unittest
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient
from PIL import Image

import app.api as api


FIELDS = {'发票号码': '00123', '开票日期': '2025年01月02日',
          '购买方名称': '测试公司', '购买方税号': None, '价税合计（小写）': '￥123.00'}


def image_b64(fmt='JPEG'):
    buffer = io.BytesIO()
    Image.new('RGB', (8, 8), 'white').save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api.app, raise_server_exceptions=False)
        self.infer = self.enterContext(patch.object(api, 'infer', return_value={'parsed': dict(FIELDS)}))
        self.ocr = Mock(return_value=([([], '可信文字', .90), ([], '低置信度', .69)], None))
        self.enterContext(patch.object(api, 'get_ocr', return_value=self.ocr))

    def request(self, **kwargs):
        return self.client.post('/extract/tax', json={'image_b64': image_b64(), **kwargs})

    def test_valid_fields_preserve_null_and_leading_zeros(self):
        response = self.request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['fields'], FIELDS)
        self.assertEqual(self.infer.call_args.args[3], ['可信文字'])

    def test_disabled_ocr_is_not_called(self):
        response = self.request(use_ocr=False)
        self.assertEqual(response.status_code, 200)
        self.ocr.assert_not_called()
        self.assertEqual(self.infer.call_args.args[3], [])

    def test_no_ocr_text_is_allowed(self):
        self.ocr.return_value = (None, None)
        self.assertEqual(self.request().status_code, 200)

    def test_invalid_field_objects_are_rejected(self):
        missing = dict(FIELDS); del missing['购买方税号']
        cases = [{}, missing, {**FIELDS, '额外字段': 'x'}, [], None,
                 {**FIELDS, '发票号码': 123}, {**FIELDS, '购买方税号': False},
                 {**FIELDS, '购买方名称': ['x']}, {**FIELDS, '购买方名称': '  '}]
        for fields in cases:
            with self.subTest(fields=fields):
                self.infer.return_value = {'parsed': fields}
                self.assertEqual(self.request(use_ocr=False).status_code, 502)

    def test_all_null_fields_are_valid(self):
        self.infer.return_value = {'parsed': dict.fromkeys(FIELDS)}
        self.assertEqual(self.request(use_ocr=False).status_code, 200)

    def test_timeout_is_504(self):
        self.infer.side_effect = httpx.ReadTimeout('private endpoint')
        response = self.request(use_ocr=False)
        self.assertEqual(response.status_code, 504)
        self.assertNotIn('private endpoint', response.text)

    def test_upstream_errors_are_502(self):
        for error in [httpx.ConnectError('private'), ValueError('bad JSON'), KeyError('choices'), TypeError('bad envelope')]:
            with self.subTest(error=type(error).__name__):
                self.infer.side_effect = error
                self.assertEqual(self.request(use_ocr=False).status_code, 502)

    def test_ocr_failure_is_503_not_bad_image(self):
        for error in [RuntimeError('private model path'), ValueError('OCR failed')]:
            self.ocr.side_effect = error
            response = self.request()
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private', response.text)
        self.infer.assert_not_called()

    def test_ocr_initialization_failure_is_503(self):
        with patch.object(api, 'get_ocr', side_effect=RuntimeError('missing weights')):
            self.assertEqual(self.request().status_code, 503)
        self.infer.assert_not_called()

    def test_upstream_http_error_is_502(self):
        self.infer.side_effect = httpx.HTTPStatusError(
            'upstream failed', request=httpx.Request('POST', 'http://localhost'),
            response=httpx.Response(500))
        self.assertEqual(self.request(use_ocr=False).status_code, 502)

    def test_bad_images_are_422(self):
        for payload in ['', '%%%', 'YQ==', image_b64('PNG')]:
            with self.subTest(payload=payload[:10]):
                self.assertEqual(self.request(image_b64=payload).status_code, 422)
        self.infer.assert_not_called()
        self.ocr.assert_not_called()

    def test_pixel_limit_is_checked_before_loading(self):
        with patch.object(api.Image, 'open') as opened:
            image = opened.return_value.__enter__.return_value
            image.format = 'JPEG'; image.width = 5000; image.height = 5000
            self.assertEqual(self.request().status_code, 422)
            image.load.assert_not_called()

    def test_request_types_and_extra_keys_are_strict(self):
        for change in [{'use_ocr': 'false'}, {'use_ocr': 1}, {'image_b64': 123}, {'extra': True}]:
            with self.subTest(change=change):
                self.assertEqual(self.request(**change).status_code, 422)

    def test_request_size_limit(self):
        self.assertEqual(self.request(image_b64='A' * 12_000_001).status_code, 422)
        self.infer.assert_not_called()


if __name__ == '__main__':
    unittest.main()
