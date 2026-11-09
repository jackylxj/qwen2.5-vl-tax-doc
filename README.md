# Multimodal Tax Document Understanding with Qwen2.5-VL

中文增值税发票图像转 JSON。使用 Qwen2.5-VL-7B-Instruct 与 RapidOCR 提取票号、日期、购买方名称、购买方税号和价税合计，并通过 vLLM 和 FastAPI 提供接口。

本仓库整理了 2026 年 11 月公开复现实验的五字段推理代码、LoRA 配置、评分方法及脱敏结果。部署配置采用基座加 OCR，LoRA 作为对照实验。

## 实测结果

| 最终独立评测 | 基座加 OCR | 追加税号栏复读 |
|---|---:|---:|
| 字段匹配 | 68/72 | 69/72 |
| 整票五字段全对 | 11/14 | 11/14 |
| 空税号正确返回 null | 1/3 | 2/3 |
| 非空税号正确 | 12/12 | 12/12 |
| 价税合计正确 | 13/14 | 13/14 |

共 15 张独立发票。14 张各计五字段，另一张日期模糊，仅计两个可核对字段。10 张数电票中有 7 张来自同一购方，结果反映这批小样本的覆盖范围。字段得分包含空值，漏键计错。原件阅核和 PDF 文本层用于建立参考答案，模型输入使用图像及重新运行的 OCR。

单张 NVIDIA A10、串行回环 API 请求的中位耗时为 5.59 秒，包含 OCR。关闭 vLLM 前缀缓存后，5 张复测逐字段复现。详细条件见 [实验记录](docs/experiment.md)，聚合指标见 [final_metrics.json](results/final_metrics.json)。

## 快速查看结果

使用 Python 3.10 及以上，在仓库根目录执行。此命令仅需标准库，打印三组已记录并脱敏的正常票、折扣票和失败票结果。

```bash
python scripts/demo.py
```

examples/recorded_cases.json 保留日期和金额，票号、税号和购买方名称替换为 redacted。原始票据、逐票个人信息、模型权重和本机连接配置保存在实验环境。获取数据和重新核验的流程见 [数据说明](docs/data.md)。

## 启动实时服务

实验环境使用 Python 3.12/3.13。以下依赖范围用于安装，具体 GPU 环境需匹配 PyTorch、CUDA 和 vLLM。公开打包版完成离线回放、评分与 API 契约检查，GPU 实测数字来自上述实验环境。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 在兼容 CUDA 的 Linux GPU 环境安装 vLLM
pip install vllm
bash scripts/serve_model.sh
```

MODEL_PATH 环境变量可指定本地 Qwen2.5-VL-7B-Instruct 权重目录。默认从模型标识加载。模型服务监听 127.0.0.1:18641，禁用前缀缓存，视觉像素上限为 501760。

另开同一环境的终端启动 CPU OCR 与网关。

```bash
uvicorn app.api:app --host 127.0.0.1 --port 18642
python scripts/demo.py --image /path/to/invoice.jpg
```

接口文档位于 http://127.0.0.1:18642/docs。POST /extract/tax 接收 image_b64 和可选的 use_ocr，默认开启 OCR。输入要求 JPEG 且不超过两千万像素，坏图返回 422，上游错误返回 502。服务默认监听回环地址，远程使用可建立 SSH 转发。

## LoRA 训练与评分

使用 LLaMA-Factory，安装方式见其官方仓库。训练参数为 rank 8、alpha 16、q_proj/v_proj、冻结视觉模块和多模态投影层、学习率 0.0001、两轮。实际实验训练 29 张广东专票，购买方税号只有一种。

准备 data/manifest.json，格式为 train 列表，每项包含 id 和 target 五字段对象。把对应图片放到 images/id.jpg，再执行以下命令。

```bash
python scripts/prepare_training.py
llamafactory-cli train configs/lora.yaml
```

使用自己的合法数据或按来源条件下载数据，先冻结划分。评分参考 JSON 使用 docs 列表，各项含 id 和 target。预测目录内为 id.json，每份含 fields 对象。可运行以下命令。

```bash
python scripts/score.py data/gold.json outputs/predictions
```

日期按年月日、金额按数值归一，票号及税号保留前导零，空栏要求 JSON null。

## 已知限制

空税号误填、票号多生成前导零以及价税合计读错列仍有发生。当前成绩对应五字段任务。整票明细、申报表和政策检索已在实验工程中做过小规模演示，独立评测和公开可复用入口仍待扩展。模型输出需要按使用场景核验。

## 参考实现与数据来源

- [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL)
- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- [RapidOCR](https://github.com/RapidAI/RapidOCR)
- [vLLM](https://github.com/vllm-project/vllm)
- [飞桨 zzsfp 数据页](https://aistudio.baidu.com/datasetdetail/165561)
- [VATID](https://github.com/FuxiJia/InvoiceDatasets)
- [电子发票解析样例](https://github.com/jiangnanboy/pdf_invoice_parser)

依赖库、模型和数据遵循各自的使用及许可条件。公开仓库代码尚未指定独立开源许可证。
