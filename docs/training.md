# Training workflow / 训练流程

The project uses LLaMA-Factory to fine-tune Qwen2.5-VL-7B-Instruct with LoRA. The public configuration freezes the vision tower and multimodal projector and targets q_proj/v_proj. Training and serving are separate: scripts/serve_model.sh serves the base model, not the LoRA adapter.

项目通过 LLaMA-Factory 对 Qwen2.5-VL-7B-Instruct 进行 LoRA 微调。公开配置冻结视觉编码器与多模态投影层，适配 q_proj/v_proj。训练与部署分开：scripts/serve_model.sh 加载基座模型，不加载 LoRA 适配器。

## Code entry points / 代码入口

- [prepare_training.py](../scripts/prepare_training.py): converts a local image/target manifest into multimodal ShareGPT records and dataset_info.json. / 将本地图像与标签清单转换为多模态 ShareGPT 数据及数据集注册文件。
- [lora.yaml](../configs/lora.yaml): model, image pixel budget, sequence length, LoRA targets, precision, and optimization settings. / 模型、图像像素上限、序列长度、LoRA 目标层、精度与优化参数。
- [score.py](../scripts/score.py): field matching and exact-document matching with date/amount normalization. / 日期金额归一化后的字段匹配与整票匹配。

## Run and retain logs / 运行与日志留存

Install a compatible LLaMA-Factory environment. Prepare authorized images and annotations, freeze data splits, review the configuration, and use a fresh output directory for each run. The preparation script does not perform deduplication or create a held-out split for you.

安装兼容的 LLaMA-Factory 环境，准备有权使用的图像与标注，固定数据划分，检查配置，并为每次训练设置新的输出目录。数据转换脚本不负责去重或自动创建独立评测集。

Run from the repository root in Bash / 在仓库根目录使用 Bash 执行：

```bash
python scripts/prepare_training.py
mkdir -p outputs
set -o pipefail
llamafactory-cli train configs/lora.yaml 2>&1 | tee outputs/train-console.log
```

For traceability, retain the exact training config, input manifest hashes, Python package versions, LLaMA-Factory commit, console output, and generated adapter configuration and weights. Trainer state and step logs depend on framework version and settings; verify the actual output directory rather than assuming they exist. Preserve original timestamps. Training loss alone does not establish held-out extraction quality.

为便于核验，应保留实际训练配置、输入清单哈希、Python 依赖版本、LLaMA-Factory 提交、控制台日志，以及生成的适配器配置和权重。训练状态与逐步日志由框架版本和配置决定，应检查实际输出目录。保留原始时间戳；训练损失下降本身不能证明独立发票上的抽取效果。

Historical training logs and invoice annotations are not distributed in the current public source tree.

当前公开源码目录不分发历史训练日志和发票标注。
