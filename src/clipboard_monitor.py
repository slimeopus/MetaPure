"""
Модуль для мониторинга буфера обмена и автоматической очистки метаданных.
"""

import time
import threading
import win32clipboard
from pathlib import Path
from typing import List, Callable
import logging
import ctypes

logger = logging.getLogger(__name__)


class ClipboardMonitor:
    """
    Класс для мониторинга буфера обмена Windows.
    """

    def __init__(self):
        self.is_monitoring = False
        self.last_clipboard_files = []
        self.on_file_copied = None  # Коллбэк для обработки скопированных файлов
        self.monitor_thread = None
        self.pause_event = threading.Event()  # Для паузы мониторинга

    def _get_clipboard_files(self) -> List[Path]:
        """
        Получает список файлов из буфера обмена.

        Returns:
            Список путей к файлам
        """
        files = []
        
        try:
            win32clipboard.OpenClipboard()
            
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                # Получаем список файлов из буфера обмена
                file_list = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                
                # Используем ctypes для доступа к DragQueryFile
                # Получаем количество файлов
                # Альтернативный способ получения файлов из буфера обмена
                try:
                    file_list = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                    for file_path in file_list:
                        if file_path:
                            files.append(Path(file_path))
                except Exception as e:
                    logger.error(f"Ошибка при обработке списка файлов из буфера обмена: {e}")
                        
        except Exception as e:
            logger.error(f"Ошибка при получении файлов из буфера обмена: {e}")
            
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
                
        return files

    def _monitor_clipboard(self):
        """
        Основной цикл мониторинга буфера обмена.
        """
        logger.info("Запущен мониторинг буфера обмена")
        
        while self.is_monitoring:
            try:
                # Проверяем, есть ли файлы в буфере обмена
                current_files = self._get_clipboard_files()
                
                # Если нашли файлы и они отличаются от предыдущих
                if current_files and current_files != self.last_clipboard_files:
                    self.last_clipboard_files = current_files
                    
                    # Вызываем коллбэк для обработки файлов
                    if self.on_file_copied:
                        try:
                            self.on_file_copied(current_files)
                        except Exception as e:
                            logger.error(f"Ошибка при вызове коллбэка on_file_copied: {e}")
                
                # Проверяем состояние паузы
                if self.pause_event.wait(timeout=0.5):  # Ждем полсекунды или сигнала паузы
                    self.pause_event.clear()
                    
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(1)  # Пауза при ошибке

        logger.info("Мониторинг буфера обмена остановлен")

    def start(self):
        """
        Запускает мониторинг буфера обмена.
        """
        if self.is_monitoring:
            logger.warning("Мониторинг буфера обмена уже запущен")
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
        self.monitor_thread.start()
        logger.info("Мониторинг буфера обмена запущен")

    def stop(self):
        """
        Останавливает мониторинг буфера обмена.
        """
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)  # Ожидаем завершения потока
            
        logger.info("Мониторинг буфера обмена остановлен")

    def pause(self):
        """
        Приостанавливает мониторинг на короткое время.
        """
        self.pause_event.set()
        
    def resume(self):
        """
        Возобновляет мониторинг после паузы.
        """
        self.pause_event.clear()