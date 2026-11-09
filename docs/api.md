# API contract and tests / 接口契约与测试

## Request / 请求

POST /extract/tax accepts image_b64 (a nonempty base64 string, at most 12,000,000 characters) and use_ocr (a boolean, default true). Unknown request keys are rejected. Images must be valid JPEGs with at most 20,000,000 pixels.

POST /extract/tax 接收 image_b64（非空 base64 字符串，最多 12,000,000 字符）和 use_ocr（布尔值，默认 true）。拒绝未知请求字段；图像必须是有效 JPEG，且不超过 20,000,000 像素。

## Response / 响应

A successful response contains model, fields, and ocr_tokens. The fields object must contain exactly 发票号码, 开票日期, 购买方名称, 购买方税号, and 价税合计（小写）. Every key is required; its value must be a nonblank string or null. Strings are preserved without numeric coercion, including leading zeros. All five null values are structurally valid and indicate no readable field values, not extraction success on those fields. Schema validation does not verify factual correctness or date/amount semantics.

成功响应包含 model、fields 和 ocr_tokens。fields 必须恰好包含发票号码、开票日期、购买方名称、购买方税号、价税合计（小写）五个字段，每个值只能是非空白字符串或 null。保留字符串原值和前导零，不自动转成数字。五个值全部为 null 在结构上合法，表示没有可读字段值，不表示字段抽取正确。结构校验不验证事实正确性或日期、金额的业务语义。

OCR is initialized lazily and skipped when use_ocr is false. Only OCR text with confidence at least 0.70 is forwarded. ocr_tokens counts raw OCR detections before filtering. An OCR failure returns an error instead of silently changing the requested pipeline.

OCR 按需初始化，use_ocr 为 false 时不加载或执行 OCR。仅传入置信度至少为 0.70 的文字；ocr_tokens 统计过滤前的检测项。OCR 故障返回错误，不静默切换推理方案。

| HTTP | Meaning / 含义 |
|---|---|
| 200 | Structurally valid five-field output / 五字段结构校验通过 |
| 422 | Invalid request, base64, image format, or size / 请求、编码、图像格式或尺寸不合法 |
| 502 | Upstream HTTP failure or invalid/incomplete model output / 上游 HTTP 失败或模型输出异常、不完整 |
| 503 | OCR initialization or execution failed / OCR 初始化或执行失败 |
| 504 | Model request timed out / 模型请求超时 |

Model output rejects wrong model identifiers, malformed completion envelopes, non-stop finish reasons, invalid JSON, duplicate JSON keys, missing/extra fields, and wrong value types. Plain JSON and a single JSON Markdown code fence are supported. Responses do not expose raw upstream exceptions.

模型输出检查模型标识、响应结构及结束原因，并拒绝无效 JSON、重复键、缺失或多余字段以及错误类型。支持纯 JSON 或单个 JSON Markdown 代码块。错误响应不透出原始上游异常。

## Offline regression tests / 离线回归测试

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Tests use generated tiny images, temporary labels, and mocked OCR/model responses. No GPU, invoice dataset, model weights, or live service is required. They cover request validation, field schema, OCR switching/filtering/failures, upstream timeouts and malformed output, and scoring normalization. Live GPU inference is a separate acceptance check.

测试使用生成的小图片、临时标签和模拟 OCR/模型响应，不依赖 GPU、发票数据集、模型权重或在线服务。覆盖请求校验、字段结构、OCR 开关与过滤及故障、模型超时与异常输出，以及评分归一化。真实 GPU 推理须另行验收。
