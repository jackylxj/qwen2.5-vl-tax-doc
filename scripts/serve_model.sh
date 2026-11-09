#!/usr/bin/env bash
set -eu
model_path="${MODEL_PATH:-Qwen/Qwen2.5-VL-7B-Instruct}"
vllm serve "$model_path" --served-model-name vat-base --host 127.0.0.1 --port 18641 --dtype bfloat16 --max-model-len 4096 --gpu-memory-utilization .9 --enforce-eager --no-enable-prefix-caching --max-num-seqs 1 --limit-mm-per-prompt '{"image":1,"video":0}' --mm-processor-kwargs '{"max_pixels":501760}'
