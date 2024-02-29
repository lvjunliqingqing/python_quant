import os
import json


def load_json(filepath: str) -> dict:
    """
    json文件读操作
    filepath:文件路径: "E:\jobs\designer_demo\python_验证\main_breed_record.json"
    """
    if os.path.isfile(filepath):
        with open(filepath, mode="r", encoding="UTF-8") as f:
            data = json.load(f)
        return data
    else:
        save_json(filepath, {})
        return {}


def save_json(filepath: str, data: dict) -> None:
    """
    json写操作
    filepath:文件路径: "E:\jobs\designer_demo\python_验证\main_breed_record.json"
    """
    with open(filepath, mode="w+", encoding="UTF-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )
