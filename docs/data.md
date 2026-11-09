# 数据准备与范围

训练来源为飞桨 zzsfp，跨省纸票来源为 VATID。使用前核对数据页及仓库的许可和适用范围。按发票号码排除重复拍摄，并按购买方或来源划分开发和评测数据。

模型只读取图片及现场 OCR。PDF 文本层可用于人工建立参考标签，评价时避免把参考字段写入提示。

最终数电票来自内蒙古政府采购公开附件，涉及工程款、电力、技术服务和成品油。旧版电子普票来自公开解析器的示例文件。公开可下载性和可再分发权限需要分别核对，本仓库提供来源，票据文件由使用者自行获取。

- [VATID 发布仓库](https://github.com/FuxiJia/InvoiceDatasets)
- [zzsfp 数据页](https://aistudio.baidu.com/datasetdetail/165561)
- [旧版电子普票样例仓库](https://github.com/jiangnanboy/pdf_invoice_parser)
- [技术服务公开附件](https://ccgp-neimenggu.gov.cn/uploader/upload/commoninfo/2024/8/15/1723703574458_6458.pdf)
- [成品油公开附件](https://ccgp-neimenggu.gov.cn/uploader/upload/commoninfo/2025/2/24/1740388848661_7578.pdf)

examples/recorded_cases.json 的票号、购买方名称和税号已统一替换为 redacted。日期和金额保留实测值。该文件用于离线解释结果，脱敏字段不能用于重新计算原始准确率。
