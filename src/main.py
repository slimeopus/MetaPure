"""
Основной модуль приложения для очистки метаданных.
"""

import os
import sys
from pathlib import Path
import logging
import threading
import time

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.metadata_scrubber import MetadataScrubber
from src.clipboard_monitor import ClipboardMonitor
# from src.notification import NotificationManager  # Модуль отключен по решению пользователя
from src.ui import ModernWindow
from src.tray_manager import TrayManager
from src.settings import SettingsManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Основная функция приложения.
    """
    logger.info("Запуск приложения MetaPure")
    
    # Создаем экземпляры компонентов
    settings_manager = SettingsManager()
    scrubber = MetadataScrubber()
    clipboard_monitor = ClipboardMonitor(settings_manager)
    ui = ModernWindow("MetaPure")
    
    # Настройка коллбэков для UI
    def on_protection_enabled():
        clipboard_monitor.start()
        logger.info("Active Protection включен")
    
    def on_protection_disabled():
        clipboard_monitor.stop()
        logger.info("Active Protection выключен")
    
    ui.set_protection_callback(on_protection_enabled, on_protection_disabled)
    
    # Настройка мониторинга буфера обмена
    def on_file_copied(files):
        for file_path in files:
            # Получаем настройки из UI, если они есть
            categories_to_remove = None
            if hasattr(ui, 'scrubber_settings') and 'categories_to_remove' in ui.scrubber_settings:
                categories_to_remove = ui.scrubber_settings['categories_to_remove']
            
            if scrubber.scrub_file(str(file_path), categories_to_remove):
                # Обновляем статистику в UI
                stats = scrubber.get_statistics()
                ui.update_stats(stats)
                
                # Уведомления отключены по решению пользователя
                # notification_manager.show_simple_notification(
                #     "Метаданные удалены",
                #     "EXIF, GPS, IPTC и другие метаданные успешно удалены",
                #     timeout=2000
                # )
                
                logger.info(f"Метаданные удалены из файла: {file_path}")

    clipboard_monitor.on_file_copied = on_file_copied
    
    logger.info("Приложение запущено и готово к работе")
    
    # Создаем менеджер трея
    tray_manager = TrayManager(
        on_show=lambda: ui.show(),
        on_exit=lambda: ui._on_closing()
    )
    
    # Запуск приложения в основном потоке
    try:
        # Показываем интерфейс
        ui.show()
        
        # Запускаем мониторинг буфера обмена
        clipboard_monitor.start()
        
        # Запускаем иконку в трее
        tray_manager.start()
        
        # Запускаем основной цикл Tkinter
        logger.info("Запуск основного цикла интерфейса")
        ui.mainloop()
        
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    
    # Очистка ресурсов
    clipboard_monitor.stop()
    
    # Остановка иконки в трее
    if 'tray_manager' in locals() and tray_manager.is_running():
        tray_manager.stop()
    

if __name__ == "__main__":
    main()