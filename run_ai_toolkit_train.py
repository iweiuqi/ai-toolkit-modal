import os
import shlex

import modal

from ai_toolkit_common import (
    DATA_MOUNT_PATH,
    GPU_TYPE,
    MODEL_VOLUME_NAME,
    PERSIST_DIR,
    TOOLKIT_ROOT,
    TRAIN_CONFIG_FILE,
    TRAIN_EXTRA_ARGS,
    TRAIN_OUTPUT_DIR,
    TRAIN_TIMEOUT_SECONDS,
    build_image,
    datasets_volume,
    model_volume,
    persist_volume,
    prepare_datasets,
    resolve_container_config_path,
    run_checked,
)


image = build_image(include_ui_build=False)

app = modal.App(
    name="ai-toolkit-train",
    image=image,
    volumes={
        PERSIST_DIR: persist_volume,
        DATA_MOUNT_PATH: datasets_volume,
        TRAIN_OUTPUT_DIR: model_volume,
    },
)


def normalize_config_path(config_value: str) -> str:
    resolved = resolve_container_config_path(config_value)
    if not resolved:
        raise ValueError(
            "缺少训练配置文件。请在 .env 中设置 AI_TOOLKIT_TRAIN_CONFIG，"
            "或在 modal run 时传入 --config-file-list-str。"
        )
    return resolved


def normalize_config_list(config_value: str) -> list[str]:
    items = [item.strip() for item in config_value.replace(";", ",").split(",") if item.strip()]
    if not items:
        raise ValueError(
            "缺少训练配置文件。请在 .env 中设置 AI_TOOLKIT_TRAIN_CONFIG，"
            "或在 modal run 时传入 --config-file-list-str。"
        )
    return [normalize_config_path(item) for item in items]


@app.function(gpu=GPU_TYPE, timeout=TRAIN_TIMEOUT_SECONDS)
def train(config_file_list_str: str = "", extra_args: str = "") -> str:
    prepare_datasets()

    config_list = normalize_config_list(config_file_list_str or TRAIN_CONFIG_FILE)

    os.makedirs(TRAIN_OUTPUT_DIR, exist_ok=True)
    env = dict(os.environ)
    env["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    env["DISABLE_TELEMETRY"] = "YES"
    env["AITK_OUTPUT_DIR"] = TRAIN_OUTPUT_DIR

    cmd = ["python", "run.py", *config_list]
    merged_extra_args = extra_args or TRAIN_EXTRA_ARGS
    if merged_extra_args:
        cmd.extend(shlex.split(merged_extra_args))

    run_checked(cmd, cwd=TOOLKIT_ROOT, env=env, label="AI-Toolkit training")

    try:
        model_volume.commit()
    except Exception as exc:
        print(f"[WARN] Could not commit model volume: {exc}")

    return (
        f"Training completed.\n"
        f"configs={', '.join(config_list)}\n"
        f"output_volume={MODEL_VOLUME_NAME}\n"
        f"output_dir={TRAIN_OUTPUT_DIR}"
    )


@app.local_entrypoint()
def main(config_file_list_str: str = "", extra_args: str = ""):
    result = train.remote(config_file_list_str=config_file_list_str, extra_args=extra_args)
    print(result)
