"""Print redacted recorded cases or send a JPEG to a running gateway."""
import argparse
import base64
import json
from pathlib import Path
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--image', type=Path)
parser.add_argument('--url', default='http://127.0.0.1:18642/extract/tax')
args = parser.parse_args()
if args.image:
    payload = json.dumps({'image_b64': base64.b64encode(args.image.read_bytes()).decode()}).encode()
    request = Request(args.url, data=payload, headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=180) as response:
        print(json.dumps(json.load(response), ensure_ascii=False, indent=2))
else:
    path = Path(__file__).resolve().parents[1] / 'examples/recorded_cases.json'
    print(path.read_text(encoding='utf-8'))
