"""Build LLaMA-Factory ShareGPT data from a local manifest and image folder."""
import json
from pathlib import Path

root = Path.cwd()
manifest = json.loads((root / 'data/manifest.json').read_text(encoding='utf-8-sig'))
prompt = (root / 'configs/invoice_prompt.txt').read_text(encoding='utf-8').strip()
records = []
for document in manifest['train']:
    image = (root / 'images' / (document['id'] + '.jpg')).resolve(strict=True)
    records.append({'messages': [
        {'role': 'user', 'content': '<image>' + prompt},
        {'role': 'assistant', 'content': json.dumps(document['target'], ensure_ascii=False, separators=(',', ':'))}
    ], 'images': [str(image)]})
directory = root / 'llf_data'
directory.mkdir(exist_ok=True)
(directory / 'invoice_train.json').write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')
info = {'invoice_train': {'file_name': 'invoice_train.json', 'formatting': 'sharegpt',
                         'columns': {'messages': 'messages', 'images': 'images'},
                         'tags': {'role_tag': 'role', 'content_tag': 'content', 'user_tag': 'user', 'assistant_tag': 'assistant'}}}
(directory / 'dataset_info.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
