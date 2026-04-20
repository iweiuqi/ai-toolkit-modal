# 配置示例

这个目录放当前仓库使用的训练配置示例。

现有文件：

- `train_lora_flux_dev_modal_minimal.yaml`：适合 Modal 的最小 FLUX LoRA 训练模板

使用方式：

1. 把 [`.env.example`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/.env.example) 中的训练配置改成：

```dotenv
AI_TOOLKIT_LOCAL_CONFIG_DIR=./config
AI_TOOLKIT_TRAIN_CONFIG=train_lora_flux_dev_modal_minimal.yaml
```

2. 按你的实际情况修改 YAML 里的：

- `name`
- `datasets[0].folder_path`
- `model.name_or_path`
- `sample.prompts`

3. 运行训练：

```powershell
modal run .\run_ai_toolkit_train.py
```

说明：

- 当前模板默认使用容器内数据集路径 `/root/ai-toolkit/data/ash`
- 这只是最小起步模板，不保证适合所有显卡和模型版本
- 如果你的 GPU 不是 24GB 级别，通常需要进一步调低分辨率、采样频率或更换模型配置
