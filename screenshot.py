import os

import config


def take(sb, directory="screenshots", prefix="screenshot"):
    if not config.DEBUG:
        return
    os.makedirs(directory, exist_ok=True)

    existing = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith(".png")]

    nums = []
    for f in existing:
        parts = f.replace(".png", "").split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            nums.append(int(parts[-1]))

    next_num = max(nums, default=0) + 1
    filename = f"{prefix}_{next_num}.png"
    path = os.path.join(directory, filename)

    sb.save_screenshot(path, folder=None, selector=None)
    print(f"Saved: {path}")
