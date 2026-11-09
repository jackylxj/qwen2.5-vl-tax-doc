import json
import re
import statistics
import unicodedata
from decimal import Decimal,InvalidOperation
from pathlib import Path
root=Path(__file__).resolve().parent
def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def normalize(k,v):
    if v is None: return None
    value=unicodedata.normalize('NFKC',str(v)).strip()
    if k=='开票日期':
        parts=re.fullmatch(r'(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?',value)
        if parts: return tuple(map(int,parts.groups()))
    if k=='价税合计（小写）':
        try: return Decimal(value.strip('¥￥元 ').replace(',',''))
        except InvalidOperation: pass
    return value

import argparse
parser = argparse.ArgumentParser(description="Score labeled fields; absent keys are incorrect.")
parser.add_argument("gold", type=Path, help="JSON with a docs list of id and target objects")
parser.add_argument("predictions", type=Path, help="Folder with id.json containing a fields object")
args = parser.parse_args()
correct = total = whole = complete = 0
for doc in read(args.gold)["docs"]:
    fields = read(args.predictions / (doc["id"] + ".json"))["fields"]
    hits = sum(key in fields and normalize(key, fields[key]) == normalize(key, value)
               for key, value in doc["target"].items())
    total += len(doc["target"])
    correct += hits
    if len(doc["target"]) == 5:
        complete += 1
        whole += hits == 5 and fields.keys() == doc["target"].keys()
print(json.dumps(dict(correct=correct, total=total, whole=whole, complete=complete)))
