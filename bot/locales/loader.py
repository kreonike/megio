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
        print(f"Loading locales from: {LOCALES_DIR}")  # Добавлено для отладки

        for lang_dir in os.listdir(LOCALES_DIR):
            lang_path = LOCALES_DIR / lang_dir
            print(f"Processing: {lang_path}")  # Добавлено для отладки

            if not lang_path.is_dir() or lang_dir.startswith('__'):
                continue

            self.locales[lang_dir] = {}
            for file in os.listdir(lang_path):
                if file.endswith('.json'):
                    file_path = lang_path / file
                    print(f"Loading file: {file_path}")  # Добавлено для отладки

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            category = file.split('.')[0]
                            data = json.load(f)
                            self.locales[lang_dir][category] = data
                            print(f"Loaded {len(data)} items from {file_path}")  # Добавлено
                    except Exception as e:
                        print(f"Error loading {file_path}: {e}")  # Добавлено
                        logger.error(f"Error loading {file_path}: {e}")

        # После загрузки выведем содержимое
        print("Loaded locales structure:", json.dumps(self.locales, indent=2, ensure_ascii=False))

    def get(self, key: str, lang: str = None, **kwargs) -> str:
        """Получает локализованную строку по ключу"""
        lang = lang or self.default_lang
        try:
            # Разделяем ключ на части
            parts = key.split('.')
            data = self.locales.get(lang, {})

            # Ищем значение по вложенным ключам
            for part in parts:
                if isinstance(data, dict):
                    data = data.get(part, {})
                else:
                    break

            # Если нашли строку - форматируем её
            if isinstance(data, str):
                return data.format(**kwargs) if kwargs else data

            # Если не нашли в текущем языке, пробуем default_lang
            if lang != self.default_lang:
                return self.get(key, self.default_lang, **kwargs)

            return key
        except Exception as e:
            logger.warning(f"Localization error for key '{key}': {e}")
            return key


i18n = LocaleLoader()

print(f"Current directory: {os.getcwd()}")
print(f"LOCALES_DIR exists: {os.path.exists(LOCALES_DIR)}")
print(f"Files in locales dir: {os.listdir(LOCALES_DIR)}")