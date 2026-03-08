import json
import os
from pathlib import Path

class SettingsManager:
    """
    Менеджер настроек для приложения очистки метаданных.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Инициализирует менеджер настроек.
        
        Args:
            config_file: Имя файла конфигурации
        """
        self.config_file = Path(config_file)
        self.settings = {}
        self.default_settings = {
            'categories_to_remove': ['location', 'device_info', 'software', 'personal'],
            'auto_clean_on_paste': True,
            'show_notifications': True,
            'smart_preview': False,
            'max_files_per_copy': 100,
            'max_file_size_mb': 100
        }
        
        # Создаем директорию для конфигурации, если её нет
        if not self.config_file.parent.exists():
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.load_settings()
    
    def load_settings(self):
        """
        Загружает настройки из файла.
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                
                # Проверяем наличие всех необходимых ключей
                for key, value in self.default_settings.items():
                    if key not in self.settings:
                        self.settings[key] = value
                        
            else:
                # Используем настройки по умолчанию
                self.settings = self.default_settings.copy()
                
        except Exception as e:
            print(f"Ошибка при загрузке настроек: {e}")
            self.settings = self.default_settings.copy()
    
    def save_settings(self):
        """
        Сохраняет настройки в файл.
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении настроек: {e}")
            return False
    
    def get(self, key: str, default=None):
        """
        Получает значение настройки по ключу.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки или значение по умолчанию
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """
        Устанавливает значение настройки.
        
        Args:
            key: Ключ настройки
            value: Значение настройки
        """
        self.settings[key] = value
        
    def update_settings(self, new_settings: dict):
        """
        Обновляет настройки.
        
        Args:
            new_settings: Словарь с новыми настройками
        """
        self.settings.update(new_settings)
        
    def get_all_settings(self):
        """
        Возвращает все настройки.
        
        Returns:
            Словарь со всеми настройками
        """
        return self.settings.copy()