"""Loopback inference for the five VAT fields and the separate tax-return trial."""
from pathlib import Path
import base64
import json
import httpx
import os

PORT = int(os.environ.get("VLLM_PORT", "18641"))
FORM_PROMPT = "读取申报表最右列本期应补（退）税（费）额，按行输出城市维护建设税、教育费附加、地方教育附加、合计。用这四个中文键，值用两位小数字符串，空格子返回null。仅返回JSON。"

def infer(image, prompt, model, words=None, max_tokens=256):
    if words:
        prompt += "\n以下为本页OCR转写，可能有错，以票面为准：" + json.dumps(words, ensure_ascii=False)[:3000]
    encoded = base64.b64encode(image).decode()
    content = [{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+encoded}},
               {"type":"text","text":prompt}]
    body = {"model":model,"messages":[{"role":"user","content":content}],"temperature":0,"max_tokens":max_tokens}
    response = httpx.post(f"http://127.0.0.1:{PORT}/v1/chat/completions",json=body,timeout=120)
    response.raise_for_status()
    data=response.json()
    if data["model"] != model:
        raise ValueError("Model name mismatch")
    raw=data["choices"][0]["message"]["content"]
    try:
        fields=json.loads(raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    except ValueError:
        fields=None
    return {"model":model,"raw":raw,"parsed":fields}

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))
