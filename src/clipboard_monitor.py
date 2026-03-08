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
import os
from settings import SettingsManager

logger = logging.getLogger(__name__)


class ClipboardMonitor:
    """
    Класс для мониторинга буфера обмена Windows.
    """

    def __init__(self, settings_manager=None):
        self.is_monitoring = False
        self.last_clipboard_files = []
        self.on_file_copied = None  # Коллбэк для обработки скопированных файлов
        self.monitor_thread = None
        self.pause_event = threading.Event()  # Для паузы мониторинга
        self.settings = settings_manager or SettingsManager()

    def _is_valid_file_path(self, file_path: Path) -> bool:
        """
        Проверяет, является ли путь к файлу безопасным для обработки.

        Args:
            file_path: Путь к файлу

        Returns:
            True если путь безопасен, иначе False
        """
        try:
            # Проверка на абсолютный путь
            if not file_path.is_absolute():
                logger.warning(f"Относительный путь в буфере обмена: {file_path}")
                return False

            # Преобразуем путь в нормализованный абсолютный путь
            resolved_path = file_path.resolve()

            # Проверка на символические и жесткие ссылки
            if file_path.is_symlink() or os.stat(file_path).st_ino != os.stat(resolved_path).st_ino:
                logger.warning(f"Обнаружена ссылка в буфере обмена: {file_path}")
                return False

            # Получаем системную директорию
            system_root = Path(os.environ['WINDIR']).resolve()
            
            # Проверка, не находится ли файл в системной директории
            if resolved_path.is_relative_to(system_root):
                logger.warning(f"Файл в системной директории: {file_path}")
                return False

            # Проверка существования файла
            if not resolved_path.exists() or not resolved_path.is_file():
                logger.warning(f"Файл не существует или не является файлом: {file_path}")
                return False

            return True
            
        except Exception as e:
            logger.error(f"Ошибка при проверке пути {file_path}: {e}")
            return False

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
                
                # Проверяем количество файлов
                if len(file_list) > self.settings.get('max_files_per_copy', 100):
                    logger.warning(f"Слишком много файлов в буфере обмена: {len(file_list)}. Ограничение: {self.settings.get('max_files_per_copy', 100)}")
                    return []
                
                # Проверяем размер каждого файла
                for file_path in file_list:
                    if file_path:
                        path_obj = Path(file_path)
                        # Проверяем размер файла
                        try:
                            file_size_mb = path_obj.stat().st_size / (1024 * 1024)
                            if file_size_mb > self.settings.get('max_file_size_mb', 100):
                                logger.warning(f"Файл слишком большой для обработки: {file_path} ({file_size_mb:.2f} MB)")
                                continue
                        except OSError as e:
                            logger.error(f"Ошибка при получении размера файла {file_path}: {e}")
                            continue
                            
                        if self._is_valid_file_path(path_obj):
                            files.append(path_obj)
                
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