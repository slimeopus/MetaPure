"""
Модуль для отображения системных уведомлений.
"""

import win32gui
import win32gui_struct
import win32con
import winerror
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class Notification:
    """
    Класс для хранения данных уведомления.
    """
    title: str
    message: str
    icon: Optional[str] = None  # Путь к иконке
    timeout: int = 3000  # Время отображения в миллисекундах


class NotificationManager:
    """
    Класс для управления системными уведомлениями Windows.
    """

    def __init__(self):
        self.hwnd = None
        self.class_name = "MetadataScrubberNotification"
        self.window_created = False

    def _create_window_class(self):
        """
        Создает класс окна для уведомлений.
        """
        wc = win32gui.WNDCLASS()
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wc.lpfnWndProc = self._wnd_proc
        wc.hInstance = win32gui.GetModuleHandle(None)
        wc.hCursor = win32gui.LoadCursor(None, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpszClassName = self.class_name
        
        try:
            win32gui.RegisterClass(wc)
            self.window_created = True
            logger.debug("Класс окна уведомлений зарегистрирован")
        except win32gui.error as e:
            if e.winerror != winerror.ERROR_CLASS_ALREADY_EXISTS:
                logger.error(f"Ошибка при регистрации класса окна: {e}")
                raise
            self.window_created = True

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """
        Процедура окна для обработки сообщений.
        """
        if msg == win32con.WM_DESTROY:
            self.hwnd = None
            return 0
        
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _create_window(self):
        """
        Создает окно для уведомлений.
        """
        if not self.window_created:
            self._create_window_class()
        
        if self.hwnd is None:
            try:
                self.hwnd = win32gui.CreateWindow(
                    self.class_name,
                    "Metadata Scrubber",
                    win32con.WS_OVERLAPPED,
                    0, 0, 0, 0,
                    0, 0, win32gui.GetModuleHandle(None), None
                )
                logger.debug("Окно уведомлений создано")
            except Exception as e:
                logger.error(f"Ошибка при создании окна уведомлений: {e}")
                
    def show_notification(self, notification: Notification) -> bool:
        """
        Отображает системное уведомление.

        Args:
            notification: Объект уведомления

        Returns:
            True, если уведомление показано успешно
        """
        try:
            self._create_window()
            
            if self.hwnd is None:
                logger.error("Не удалось создать окно для уведомления")
                return False

            # Показываем баллонное уведомление
            flags = win32gui.NIIF_INFO
            
            if notification.icon == "warning":
                flags = win32gui.NIIF_WARNING
            elif notification.icon == "error":
                flags = win32gui.NIIF_ERROR
            
            win32gui.Shell_NotifyIcon(
                win32gui.NIM_MODIFY,
                (self.hwnd, 0, win32gui.NIF_INFO,
                 win32con.WM_USER + 1,
                 None, "", notification.message, notification.timeout, notification.title, flags)
            )
            
            logger.info(f"Показано уведомление: {notification.title} - {notification.message}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при показе уведомления: {e}")
            return False

    def show_simple_notification(self, title: str, message: str, timeout: int = 3000) -> bool:
        """
        Показывает простое уведомление.

        Args:
            title: Заголовок уведомления
            message: Текст сообщения
            timeout: Время отображения в миллисекундах

        Returns:
            True, если уведомление показано успешно
        """
        notification = Notification(title=title, message=message, timeout=timeout)
        return self.show_notification(notification)

    def cleanup(self):
        """
        Очищает ресурсы.
        """
        if self.hwnd:
            try:
                win32gui.DestroyWindow(self.hwnd)
                self.hwnd = None
                logger.debug("Окно уведомлений уничтожено")
            except Exception as e:
                logger.error(f"Ошибка при уничтожении окна уведомлений: {e}")