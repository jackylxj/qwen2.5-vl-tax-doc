"""Portable invoice-only entry point for the evaluated base + OCR pipeline."""
import base64
import binascii
import io
from pathlib import Path
from threading import Lock
from functools import lru_cache

import httpx
import numpy as np
from fastapi import FastAPI, HTTPException
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from app.infer import infer
from app.schema import InvoiceFields

app = FastAPI(title='Qwen2.5-VL Chinese VAT extraction')
lock = Lock()
PROMPT = (Path(__file__).resolve().parents[1] / 'configs/invoice_prompt.txt').read_text(encoding='utf-8').strip()

class ExtractionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    image_b64: str = Field(min_length=1, max_length=12_000_000)
    use_ocr: StrictBool = True


class ExtractionResponse(BaseModel):
    model: str
    fields: InvoiceFields
    ocr_tokens: int


@lru_cache(maxsize=1)
def get_ocr():
    # Initialize on first use so disabled OCR and offline tests need no weights.
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)

@app.post('/extract/tax', response_model=ExtractionResponse)
def extract(request: ExtractionRequest):
    try:
        raw = base64.b64decode(request.image_b64, validate=True)
        with Image.open(io.BytesIO(raw)) as image:
            if image.format != 'JPEG' or image.width * image.height > 20_000_000:
                raise ValueError('Expected JPEG within size limit')
            image.load()
            pixels = np.asarray(image.convert('RGB')) if request.use_ocr else None
    except (ValueError, binascii.Error, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, 'Invalid JPEG') from exc
    tokens = []
    words = []
    if request.use_ocr:
        try:
            with lock:
                tokens = get_ocr()(pixels)[0] or []
            words = [text for _, text, confidence in tokens if confidence >= .70]
        except Exception as exc:
            # OCR initialization/runtime errors are service failures, not bad JPEGs.
            raise HTTPException(503, 'OCR unavailable') from exc
    try:
        result = infer(raw, PROMPT, 'vat-base', words)
        fields = InvoiceFields.model_validate(result['parsed'])
    except httpx.TimeoutException as exc:
        raise HTTPException(504, 'Inference timed out') from exc
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(502, 'Invalid upstream response') from exc
    return {'model': 'vat-base', 'fields': fields, 'ocr_tokens': len(tokens)}
