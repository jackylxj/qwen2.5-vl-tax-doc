# Data notes / 数据说明

Development used the public Paddle zzsfp dataset, VATID paper invoice material, and invoices available in public procurement documents. These sources do not establish access to internal tax-authority systems.

项目开发使用飞桨 zzsfp 公开数据、VATID 纸质发票材料及公开采购文件中的发票。这些来源不代表获得了税务机关内部系统的数据访问权限。

Invoice images, annotations, recorded cases, and evaluation outputs are not included in the current source tree. Prepare inputs separately under their source terms, deduplicate by invoice number, and separate training, development, and evaluation data before model work.

当前源码目录不包含发票图片、标注、历史案例及评测输出。请遵循数据来源的使用条件自行准备输入，按票号去重，并在模型实验前分离训练、开发与评测数据。
