"""
Модуль для управления иконкой в системном трее.
"""

import threading
import pystray
from PIL import Image
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TrayManager:
    """
    Класс для управления иконкой приложения в системном трее.
    """

    def __init__(self, on_show: callable, on_exit: callable):
        """
        Инициализирует менеджер трея.

        Args:
            on_show: Функция, вызываемая при нажатии "Показать"
            on_exit: Функция, вызываемая при выходе из приложения
        """
        self.on_show = on_show
        self.on_exit = on_exit
        self.icon = None
        self.thread = None
        
        # Загружаем иконку
        self.image = self._load_icon()
        
    def _load_icon(self) -> Image.Image:
        """
        Загружает иконку для системного трея.

        Returns:
            Объект изображения для иконки
        """
        try:
            # Попробуем найти иконку в папке assets
            assets_dir = Path(__file__).parent.parent / "assets"
            icon_path = assets_dir / "icon.png"
            
            if icon_path.exists():
                return Image.open(str(icon_path))
        except Exception as e:
            logger.warning(f"Не удалось загрузить пользовательскую иконку: {e}")
        
        # Создаем простую зеленую иконку как fallback
        try:
            image = Image.new('RGB', (64, 64), color=(0, 255, 0))
            return image
        except Exception as e:
            logger.error(f"Не удалось создать fallback иконку: {e}")
            return None

    def _create_menu(self) -> pystray.Menu:
        """
        Создает меню для иконки в трее.

        Returns:
            Объект меню pystray
        """
        return pystray.Menu(
            pystray.MenuItem('Показать', self._on_show),
            pystray.MenuItem('Выход', self._on_exit)
        )

    def _on_show(self, icon, item):
        """
        Обработчик нажатия на пункт "Показать".
        """
        logger.info("Показываем главное окно по запросу из трея")
        if self.on_show:
            self.on_show()

    def _on_exit(self, icon, item):
        """
        Обработчик нажатия на пункт "Выход".
        """
        logger.info("Выход из приложения по запросу из трея")
        if self.on_exit:
            self.on_exit()
        
        # Останавливаем иконку в трее
        icon.stop()

    def start(self):
        """
        Запускает иконку в системном трее в отдельном потоке.
        """
        if self.icon is not None:
            return
            
        # Создаем иконку
        self.icon = pystray.Icon(
            "metadata_scrubber",
            self.image,
            "Metadata Scrubber",
            self._create_menu()
        )
        
        # Запускаем в отдельном потоке
        self.thread = threading.Thread(target=self._run_icon, daemon=True)
        self.thread.start()
        
        logger.info("Иконка в системном трее запущена")

    def _run_icon(self):
        """
        Запускает цикл иконки.
        """
        try:
            self.icon.run()
        except Exception as e:
            logger.error(f"Ошибка при работе иконки в трее: {e}")

    def stop(self):
        """
        Останавливает иконку в системном трее.
        """
        if self.icon is not None:
            try:
                self.icon.stop()
                logger.info("Иконка в системном трее остановлена")
            except Exception as e:
                logger.error(f"Ошибка при остановке иконки в трее: {e}")
            
        if self.thread is not None:
            # Дожидаемся завершения потока
            self.thread.join(timeout=2)
            
    def is_running(self) -> bool:
        """
        Проверяет, запущена ли иконка в трее.

        Returns:
            True, если иконка запущена
        """
        return self.icon is not None and self.thread is not None and self.thread.is_alive()