import threading
import time

import modal

from ai_toolkit_common import (
    AI_TOOLKIT_AUTH,
    COMMIT_INTERVAL_SECONDS,
    DATA_MOUNT_PATH,
    DB_PATH,
    GPU_TYPE,
    OUTPUT_PATH,
    PERSIST_DIR,
    UI_PORT,
    UI_ROOT,
    UI_TIMEOUT_SECONDS,
    build_image,
    datasets_volume,
    persist_volume,
    prepare_datasets,
    replace_with_symlink,
    run_checked,
)


image = build_image(include_ui_build=True)

app = modal.App(
    name="ai-toolkit-ui",
    image=image,
    volumes={
        PERSIST_DIR: persist_volume,
        DATA_MOUNT_PATH: datasets_volume,
    },
)


@app.function(gpu=GPU_TYPE, timeout=UI_TIMEOUT_SECONDS)
@modal.web_server(UI_PORT)
def ui():
    import os
    import subprocess

    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    os.environ["DISABLE_TELEMETRY"] = "YES"
    if AI_TOOLKIT_AUTH:
        os.environ["AI_TOOLKIT_AUTH"] = AI_TOOLKIT_AUTH

    os.makedirs(PERSIST_DIR, exist_ok=True)

    persistent_output = os.path.join(PERSIST_DIR, "output")
    os.makedirs(persistent_output, exist_ok=True)

    persistent_db = os.path.join(PERSIST_DIR, "aitk_db.db")
    if not os.path.exists(persistent_db):
        open(persistent_db, "ab").close()

    replace_with_symlink(OUTPUT_PATH, persistent_output)
    replace_with_symlink(DB_PATH, persistent_db)
    prepare_datasets()

    worker_env = dict(os.environ)
    worker_env["NODE_ENV"] = "production"
    worker_env["DATABASE_URL"] = f"file:{persistent_db}"

    run_checked(["npx", "prisma", "generate"], cwd=UI_ROOT, env=worker_env, label="Prisma generate")
    run_checked(
        ["npx", "prisma", "db", "push", "--skip-generate"],
        cwd=UI_ROOT,
        env=worker_env,
        label="Prisma db push",
    )

    def commit_loop() -> None:
        while True:
            time.sleep(COMMIT_INTERVAL_SECONDS)
            try:
                persist_volume.commit()
            except Exception:
                pass
            try:
                datasets_volume.commit()
            except Exception:
                pass

    threading.Thread(target=commit_loop, daemon=True).start()

    worker_process = subprocess.Popen(["node", "dist/cron/worker.js"], cwd=UI_ROOT, env=worker_env)
    web_process = subprocess.Popen(
        ["npx", "next", "start", "--port", str(UI_PORT), "--hostname", "0.0.0.0"],
        cwd=UI_ROOT,
        env=worker_env,
    )

    try:
        web_process.wait()
    finally:
        worker_process.terminate()
