# AI Toolkit Modal

这个仓库用于把 `ostris/ai-toolkit` 部署到 Modal，当前同时支持：

- Web UI 部署
- 配置驱动的训练任务执行

## 目录说明

- [`ai_toolkit_common.py`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/ai_toolkit_common.py)：公共配置、镜像构建和数据同步逻辑
- [`run_ai_toolkit_ui.py`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/run_ai_toolkit_ui.py)：UI 入口脚本
- [`run_ai_toolkit_train.py`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/run_ai_toolkit_train.py)：训练入口脚本
- [`config`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/config)：训练配置示例目录
- [`data`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/data)：本地示例数据目录，启动时会同步到 Modal 数据集 Volume
- [`.env.example`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/.env.example)：环境变量模板
- [`requirements.txt`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/requirements.txt)：本地依赖

## 本地前置要求

- Python 3.10+
- 可用的 Modal 账号

安装依赖：

```powershell
python -m pip install -r .\requirements.txt
```

登录 Modal：

```powershell
python -m modal setup
```

## 配置

仓库根目录已提供 [`.env`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/.env)。

常用配置项：

- `AI_TOOLKIT_UI_PORT`：容器内 UI 端口，默认 `8675`
- `AI_TOOLKIT_GPU`：Modal GPU 类型，默认 `L4`
- `AI_TOOLKIT_TIMEOUT`：UI 函数超时秒数，默认 `86400`
- `AI_TOOLKIT_TRAIN_TIMEOUT`：训练函数超时秒数，默认 `7200`
- `AI_TOOLKIT_UI_VOLUME`：UI 持久化 Volume 名称
- `AI_TOOLKIT_DATA_VOLUME`：数据集 Volume 名称
- `AI_TOOLKIT_MODEL_VOLUME`：训练输出 Volume 名称
- `AI_TOOLKIT_VOLUME_COMMIT_INTERVAL`：Volume 自动提交间隔
- `AI_TOOLKIT_AUTH`：可选 UI 密码
- `AI_TOOLKIT_LOCAL_DATA_FOLDER`：启动时同步到数据集 Volume 的本地目录
- `AI_TOOLKIT_LOCAL_DATASET_SOURCE`：可选额外数据目录，只在目标不存在时补充导入
- `AI_TOOLKIT_LOCAL_CONFIG_DIR`：训练配置目录，会挂载到容器 `/root/local_configs`
- `AI_TOOLKIT_TRAIN_CONFIG`：训练默认配置文件，可用逗号分隔多个配置
- `AI_TOOLKIT_TRAIN_EXTRA_ARGS`：训练附加参数
- `AI_TOOLKIT_TRAIN_OUTPUT_DIR`：容器内训练输出目录，默认 `/root/ai-toolkit/modal_output`，UI 会映射到 `/root/ai-toolkit/output`

说明：

- `AI_TOOLKIT_LOCAL_DATA_FOLDER=./datasets` 时，会把仓库内 [`datasets`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/datasets) 同步到 Modal 数据集 Volume。
- `AI_TOOLKIT_LOCAL_DATASET_SOURCE` 适合指向一个更大的本地数据集目录，已有同名数据集时不会覆盖。
- `AI_TOOLKIT_LOCAL_CONFIG_DIR` 适合放置你自己的 YAML 配置文件。
- `AI_TOOLKIT_TRAIN_CONFIG` 可以写绝对容器路径，也可以写相对于 `AI_TOOLKIT_LOCAL_CONFIG_DIR` 的路径；多个配置可用逗号分隔。

## 启动 UI

Windows PowerShell 推荐先启用 UTF-8：

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

启动 UI：

```powershell
modal serve .\run_ai_toolkit_ui.py
```

启动后，Modal 会输出一个公开访问地址。

## 运行训练任务

先在 [`.env`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/.env) 中配置训练项，例如：

```dotenv
AI_TOOLKIT_LOCAL_CONFIG_DIR=./config
AI_TOOLKIT_TRAIN_CONFIG=train_lora_flux_dev_modal_minimal.yaml
AI_TOOLKIT_MODEL_VOLUME=ai-toolkit-models
```

然后执行：

```powershell
modal run .\run_ai_toolkit_train.py
```

如果要临时覆盖配置文件或补充参数：

```powershell
modal run .\run_ai_toolkit_train.py -- --config-file-list-str=job1.yaml,job2.yaml --extra-args="--sample_every_n_steps 100"
```

训练脚本会：

- 同步本地 `data` 到数据集 Volume
- 读取本地配置目录中的 YAML
- 在容器内执行 `python run.py <config>`
- 把训练输出写入 `AI_TOOLKIT_MODEL_VOLUME`

仓库内已提供最小可跑模板：

- [`config/train_lora_flux_dev_modal_minimal.yaml`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/config/train_lora_flux_dev_modal_minimal.yaml)

这个模板基于上游 `ai-toolkit` 的 FLUX LoRA 示例思路调整而来，默认使用本仓库的 `ash` 数据集路径 `/root/ai-toolkit/datasets/ash`。参考上游文档与示例：

- https://github.com/ostris/ai-toolkit
- https://github.com/ostris/ai-toolkit/blob/main/run.py
- https://github.com/ostris/ai-toolkit/blob/main/config/examples/train_lora_wan21_1b_24gb.yaml

## 数据持久化

使用三个 Modal Volume：

- `AI_TOOLKIT_UI_VOLUME`：持久化数据库和输出目录
- `AI_TOOLKIT_DATA_VOLUME`：持久化数据集目录
- `AI_TOOLKIT_MODEL_VOLUME`：持久化训练输出

容器内对应路径：

- 数据库：`/root/ai-toolkit/aitk_db.db`
- 输出：`/root/ai-toolkit/output`
- 数据集：`/root/ai-toolkit/datasets`
- 训练输出：由 `AI_TOOLKIT_TRAIN_OUTPUT_DIR` 指定，默认 `/root/ai-toolkit/modal_output`

## 当前实现行为

- `.env` 会在脚本启动时自动加载
- 本地 `data` 目录会在镜像构建时拷入，并在启动时同步到数据集 Volume
- UI 和训练共享同一套公共配置与数据同步逻辑

## 排错建议

- 如果 `modal serve` 或 `modal run` 失败，先确认已执行 `python -m modal setup`
- 如果首次构建很慢，这是因为容器内需要安装 PyTorch、Node.js 和 AI-Toolkit 依赖
- 如果本地数据目录未生效，检查 [`.env`](/C:/Users/Xiao/Desktop/github/ai-toolkit-modal/.env) 中的路径是否真实存在
- 如果训练配置未找到，优先检查 `AI_TOOLKIT_LOCAL_CONFIG_DIR` 和 `AI_TOOLKIT_TRAIN_CONFIG`
