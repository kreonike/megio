# bot/locales/loader.py
import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger("bot")

BASE_DIR = Path(__file__).resolve().parent.parent
LOCALES_DIR = BASE_DIR / "locales"

class LocaleLoader:
    def __init__(self, default_lang: str = "ru"):
        self.default_lang = default_lang
        self.locales = {}
        self._load_locales()

    def _load_locales(self):
        logger.info(f"Loading locales from: {LOCALES_DIR}")
        print(f"Loading locales from: {LOCALES_DIR}")

        if not os.path.exists(LOCALES_DIR):
            logger.error(f"Locales directory does not exist: {LOCALES_DIR}")
            print(f"ERROR: Locales directory does not exist: {LOCALES_DIR}")
            return

        for lang_dir in os.listdir(LOCALES_DIR):
            lang_path = LOCALES_DIR / lang_dir
            logger.info(f"Processing language directory: {lang_path}")
            print(f"Processing: {lang_path}")

            if not lang_path.is_dir() or lang_dir.startswith('__'):
                continue

            self.locales[lang_dir] = {}
            for file in os.listdir(lang_path):
                if file.endswith('.json'):
                    file_path = lang_path / file
                    logger.info(f"Loading file: {file_path}")
                    print(f"Loading file: {file_path}")

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            category = file.split('.')[0]  # "buttons", "messages", "help"
                            data = json.load(f)
                            self.locales[lang_dir][category] = data  # Сохраняем под именем категории
                            logger.info(f"Loaded {len(data)} items from {file_path}")
                            print(f"Loaded {len(data)} items from {file_path}")
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
                        print(f"Error loading {file_path}: {e}")

        if not self.locales.get("ru"):
            logger.error("Russian locale not loaded!")
            print("ERROR: Russian locale not loaded!")
        logger.info("Loaded locales structure: %s", json.dumps(self.locales, indent=2, ensure_ascii=False))
        print("Loaded locales structure:", json.dumps(self.locales, indent=2, ensure_ascii=False))

    def get(self, key: str, lang: str = None, **kwargs) -> str:
        lang = lang or self.default_lang
        try:
            parts = key.split('.')
            data = self.locales.get(lang, {})
            for part in parts:
                if isinstance(data, dict):
                    data = data.get(part, {})
                else:
                    break
            if isinstance(data, str):
                return data.format(**kwargs) if kwargs else data
            if lang != self.default_lang:
                return self.get(key, self.default_lang, **kwargs)
            logger.warning(f"Localization key '{key}' not found in lang '{lang}'")
            return key
        except Exception as e:
            logger.warning(f"Localization error for key '{key}': {e}")
            return key

i18n = LocaleLoader()

print(f"Current directory: {os.getcwd()}")
print(f"LOCALES_DIR exists: {os.path.exists(LOCALES_DIR)}")
print(f"Files in locales dir: {os.listdir(LOCALES_DIR)}")