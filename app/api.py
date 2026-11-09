"""Portable invoice-only entry point for the evaluated base + OCR pipeline."""
import base64
import binascii
import io
from pathlib import Path
from threading import Lock

import httpx
import numpy as np
from fastapi import FastAPI, HTTPException
from PIL import Image
from pydantic import BaseModel, Field
from rapidocr_onnxruntime import RapidOCR
from app.infer import infer

app = FastAPI(title='Qwen2.5-VL Chinese VAT extraction')
engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
lock = Lock()
PROMPT = (Path(__file__).resolve().parents[1] / 'configs/invoice_prompt.txt').read_text(encoding='utf-8').strip()

class ExtractionRequest(BaseModel):
    image_b64: str = Field(max_length=12_000_000)
    use_ocr: bool = True

@app.post('/extract/tax')
def extract(request: ExtractionRequest):
    try:
        raw = base64.b64decode(request.image_b64, validate=True)
        with Image.open(io.BytesIO(raw)) as image:
            if image.format != 'JPEG' or image.width * image.height > 20_000_000:
                raise ValueError('Expected JPEG within size limit')
            image.load()
            with lock:
                tokens = (engine(np.asarray(image.convert('RGB')))[0] or []) if request.use_ocr else []
    except (ValueError, binascii.Error, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, 'Invalid JPEG') from exc
    try:
        result = infer(raw, PROMPT, 'vat-base', [text for _, text, confidence in tokens if confidence >= .70])
        if not isinstance(result['parsed'], dict):
            raise ValueError('Expected JSON object')
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
        raise HTTPException(502, 'Invalid upstream response') from exc
    return {'model': 'vat-base', 'fields': result['parsed'], 'ocr_tokens': len(tokens)}
