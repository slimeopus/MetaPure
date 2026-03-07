"""
Модуль для реализации пользовательского интерфейса.
"""

import sys
import time
import threading
from typing import Dict, Callable
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
import ctypes
from pathlib import Path
import json
import os

# Для поддержки высокого DPI
ctypes.windll.shcore.SetProcessDpiAwareness(1)

logger = __import__('logging').getLogger(__name__)

@dataclass
class UIConfig:
    """
    Конфигурация интерфейса.
    """
    theme: str = "dark"
    accent_color: str = "#00FF00"  # Зеленый для защиты
    bg_color: str = "#1e1e1e"
    fg_color: str = "#ffffff"
    font_family: str = "Segoe UI"
    font_size: int = 12


class ModernWindow(tk.Tk):
    """
    Современный интерфейс для приложения очистки метаданных.
    """
    
    def get_setting(self, key: str, default=None):
        """
        Получает значение настройки из конфигурационного файла.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки или значение по умолчанию
        """
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get(key, default)
        except Exception as e:
            logger.error(f"Ошибка при загрузке настроек: {e}")
            
        return default

    def __init__(self, title: str = "Metadata Scrubber", config: UIConfig = None):
        super().__init__()
        
        self.config = config or UIConfig()
        self.title(title)
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Настройка окна
        self._setup_window()
        
        # Создание интерфейса
        self._create_widgets()
        
        # Состояние пульсации
        self.pulse_active = False
        self.pulse_alpha = 0.3
        self.pulse_direction = 0.02
        
        # Загрузка настроек при запуске
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    self.scrubber_settings = json.load(f)
                logger.info("Настройки загружены из файла")
            except Exception as e:
                logger.error(f"Ошибка при загрузке настроек: {e}")
                self.scrubber_settings = {}
        else:
            self.scrubber_settings = {}

    def _setup_window(self):
        """
        Настраивает базовые свойства окна.
        """
        # Установка стиля
        self.configure(bg=self.config.bg_color)
        
        # Центрирование окна
        self._center_window()

    def _center_window(self):
        """
        Центрирует окно на экране.
        """
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        """
        Создает виджеты интерфейса.
        """
        # Основной фрейм
        self.main_frame = tk.Frame(self, bg=self.config.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок
        self.title_label = tk.Label(
            self.main_frame,
            text="Metadata Scrubber",
            font=(self.config.font_family, 16, "bold"),
            bg=self.config.bg_color,
            fg=self.config.fg_color
        )
        self.title_label.pack(pady=(0, 20))
        
        # Кнопка Active Protection
        self.protection_button = tk.Button(
            self.main_frame,
            text="ПРОТЕКЦИЯ: ВЫКЛ",
            font=(self.config.font_family, 12, "bold"),
            bg="#3a3a3a",
            fg=self.config.fg_color,
            relief=tk.FLAT,
            height=2,
            width=25,
            command=self._toggle_protection
        )
        self.protection_button.pack(pady=(20, 15))
        
        # Фрейм для карточек статистики
        self.stats_frame = tk.Frame(self.main_frame, bg=self.config.bg_color)
        self.stats_frame.pack(fill=tk.X, pady=(10, 15), padx=10)
        
        # Карточки статистики
        self._create_stats_cards()
        
        # Кнопка настроек
        self.settings_button = tk.Button(
            self,
            text="⚙",
            font=(self.config.font_family, 12, "bold"),
            bg=self.config.bg_color,
            fg="#888888",
            relief=tk.FLAT,
            width=3,
            height=1,
            command=self._open_settings
        )
        self.settings_button.place(relx=0.95, rely=0.02, anchor=tk.NE)
        

        
        # Привязка событий для кнопки настроек
        # self.settings_button.bind("<Enter>", lambda e: self.settings_button.config(fg="#ffffff"))
        # self.settings_button.bind("<Leave>", lambda e: self.settings_button.config(fg="#888888"))
        
        # Обработка закрытия окна
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Установка фокуса
        self.focus_force()

    def _create_stats_cards(self):
        """
        Создает карточки статистики.
        """
        stats_data = [
            ("Очищено: 0", "cleaned_files"),
            ("Геотеги: 0", "geotags"),
            ("Последнее: -", "last_action")
        ]
        
        for i, (text, key) in enumerate(stats_data):
            frame = tk.Frame(
                self.stats_frame,
                bg="#2a2a2a",
                relief=tk.RAISED,
                bd=1
            )
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            
            label = tk.Label(
                frame,
                text=text,
                font=(self.config.font_family, 10),
                bg="#2a2a2a",
                fg=self.config.fg_color,
                width=12
            )
            label.pack(padx=8, pady=4)
            
            # Сохраняем ссылку на label для обновления
            if not hasattr(self, 'stats_labels'):
                self.stats_labels = {}
            self.stats_labels[key] = label
            
            # Растягиваем колонки
            self.stats_frame.grid_columnconfigure(i, weight=1)

    def _toggle_protection(self):
        """
        Переключает состояние защиты.
        """
        current_text = self.protection_button.cget("text")
        
        if "ВЫКЛ" in current_text:
            self.protection_button.config(
                text="ПРОТЕКЦИЯ: ВКЛ",
                bg=self.config.accent_color,
                fg="#000000"
            )
            self.pulse_active = True
            # Отключаем анимацию пульсации по решению пользователя
            # self._start_pulse_animation()
            
            if hasattr(self, 'on_protection_enabled') and self.on_protection_enabled:
                self.on_protection_enabled()
                
        else:
            self.protection_button.config(
                text="ПРОТЕКЦИЯ: ВЫКЛ",
                bg="#3a3a3a",
                fg=self.config.fg_color
            )
            self.pulse_active = False
            
            if hasattr(self, 'on_protection_disabled') and self.on_protection_disabled:
                self.on_protection_disabled()

    # Метод _start_pulse_animation был отключен по решению пользователя
    # def _start_pulse_animation(self):
    #     """
    #     Запускает анимацию пульсации вокруг кнопки.
    #     """
    #     if self.pulse_active:
    #         # Изменяем прозрачность обводки (имитация пульсации)
    #         self.protection_button.config(
    #             highlightthickness=3,
    #             highlightbackground=self.config.accent_color,
    #             highlightcolor=self.config.accent_color
    #         )
    #         
    #         # Меняем толщину обводки для эффекта пульсации
    #         thickness = 2 + (self.pulse_alpha * 3)
    #         self.protection_button.config(highlightthickness=int(thickness))
    #         
    #         # Обновляем альфа-канал
    #         self.pulse_alpha += self.pulse_direction
    #         if self.pulse_alpha > 1.0:
    #             self.pulse_alpha = 1.0
    #             self.pulse_direction = -0.02
    #         elif self.pulse_alpha < 0.3:
    #             self.pulse_alpha = 0.3
    #             self.pulse_direction = 0.02

    #         # Планируем следующий кадр анимации
    #         self.after(50, self._start_pulse_animation)

    def _on_closing(self):
        """
        Обработчик закрытия окна.
        """
        self.pulse_active = False
        self.withdraw()  # Скрываем окно вместо закрытия
    
    def _open_settings(self):
        """
        Открывает окно настроек.
        """
        # Создаем модальное окно
        settings_window = tk.Toplevel(self)
        settings_window.title("Настройки")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.config.bg_color)
        settings_window.transient(self)
        settings_window.grab_set()
        
        # Центрируем окно
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Заголовок
        title_label = tk.Label(
            settings_window,
            text="Настройки очистки метаданных",
            font=(self.config.font_family, 14, "bold"),
            bg=self.config.bg_color,
            fg=self.config.fg_color
        )
        title_label.pack(pady=(20, 10))
        
        # Описание
        desc_label = tk.Label(
            settings_window,
            text="Выберите типы метаданных, которые хотите удалять",
            font=(self.config.font_family, 10),
            bg=self.config.bg_color,
            fg="#888888"
        )
        desc_label.pack(pady=(0, 20))
        
        # Фрейм для чекбоксов
        checkboxes_frame = tk.Frame(settings_window, bg=self.config.bg_color)
        checkboxes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Чекбоксы для выбора категорий
        self.location_var = tk.BooleanVar(value=True)
        self.device_var = tk.BooleanVar(value=True)
        self.software_var = tk.BooleanVar(value=True)
        self.personal_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(
            checkboxes_frame,
            text="📍 Геолокация (GPS, координаты)",
            variable=self.location_var,
            bg=self.config.bg_color,
            fg=self.config.fg_color,
            selectcolor="#2a2a2a",
            activebackground=self.config.bg_color,
            font=(self.config.font_family, 10)
        ).pack(anchor="w", pady=5)
        
        tk.Checkbutton(
            checkboxes_frame,
            text="📱 Информация об устройстве (камера, модель)",
            variable=self.device_var,
            bg=self.config.bg_color,
            fg=self.config.fg_color,
            selectcolor="#2a2a2a",
            activebackground=self.config.bg_color,
            font=(self.config.font_family, 10)
        ).pack(anchor="w", pady=5)
        
        tk.Checkbutton(
            checkboxes_frame,
            text="⚙️ Информация о программном обеспечении",
            variable=self.software_var,
            bg=self.config.bg_color,
            fg=self.config.fg_color,
            selectcolor="#2a2a2a",
            activebackground=self.config.bg_color,
            font=(self.config.font_family, 10)
        ).pack(anchor="w", pady=5)
        
        tk.Checkbutton(
            checkboxes_frame,
            text="👤 Персональная информация (автор, комментарии)",
            variable=self.personal_var,
            bg=self.config.bg_color,
            fg=self.config.fg_color,
            selectcolor="#2a2a2a",
            activebackground=self.config.bg_color,
            font=(self.config.font_family, 10)
        ).pack(anchor="w", pady=5)
        
        # Добавляем чекбокс для Smart Preview
        self.smart_preview_var = tk.BooleanVar(value=self.get_setting('smart_preview', False))
        tk.Checkbutton(
            checkboxes_frame,
            text="🔍 Smart Preview (предпросмотр изменений)",
            variable=self.smart_preview_var,
            bg=self.config.bg_color,
            fg=self.config.fg_color,
            selectcolor="#2a2a2a",
            activebackground=self.config.bg_color,
            font=(self.config.font_family, 10)
        ).pack(anchor="w", pady=5)
        
        # Кнопки
        buttons_frame = tk.Frame(settings_window, bg=self.config.bg_color)
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(
            buttons_frame,
            text="Сохранить",
            font=(self.config.font_family, 10, "bold"),
            bg=self.config.accent_color,
            fg="#000000",
            relief=tk.FLAT,
            height=2,
            width=10,
            command=lambda: self._save_settings(settings_window)
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(
            buttons_frame,
            text="Отмена",
            font=(self.config.font_family, 10),
            bg="#3a3a3a",
            fg=self.config.fg_color,
            relief=tk.FLAT,
            height=2,
            width=10,
            command=settings_window.destroy
        ).pack(side=tk.RIGHT)
        
        # Фокус на окно
        settings_window.focus_force()

    def update_stats(self, stats: Dict):
        """
        Обновляет отображение статистики.

        Args:
            stats: Словарь со статистикой
        """
        if hasattr(self, 'stats_labels'):
            # Очищено файлов
            if 'cleaned_files' in stats:
                self.stats_labels['cleaned_files'].config(
                    text=f"Очищено: {stats['cleaned_files']}"
                )
            
            # Удалено геотегов
            if 'removed_geotags' in stats:
                self.stats_labels['geotags'].config(
                    text=f"Геотеги: {stats['removed_geotags']}"
                )
            
            # Последнее действие
            if 'last_action' in stats and stats['last_action']:
                # Обрезаем длинные имена файлов
                filename = stats['last_action']
                if len(filename) > 12:
                    filename = filename[:9] + "..."
                self.stats_labels['last_action'].config(
                    text=f"Последнее: {filename}"
                )
    
    def _save_settings(self, settings_window):
        """
        Сохраняет настройки и закрывает окно.

        Args:
            settings_window: Окно настроек
        """
        # Собираем выбранные категории
        selected_categories = []
        if self.location_var.get():
            selected_categories.append('location')
        if self.device_var.get():
            selected_categories.append('device_info')
        if self.software_var.get():
            selected_categories.append('software')
        if self.personal_var.get():
            selected_categories.append('personal')
        
        # Сохраняем настройки в экземпляр класса
        if not hasattr(self, 'scrubber_settings'):
            self.scrubber_settings = {}
        self.scrubber_settings['categories_to_remove'] = selected_categories
        self.scrubber_settings['smart_preview'] = self.smart_preview_var.get()
        
        # Сохраняем настройки в файл
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.scrubber_settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек в файл: {e}")
        
        # Закрываем окно
        settings_window.destroy()
        
        logger.info(f"Настройки сохранены: {selected_categories}")

    def set_protection_callback(
        self, 
        on_enabled: Callable[[], None], 
        on_disabled: Callable[[], None]
    ):
        """
        Устанавливает коллбэки для включения и отключения защиты.

        Args:
            on_enabled: Функция, вызываемая при включении защиты
            on_disabled: Функция, вызываемая при отключении защиты
        """
        self.on_protection_enabled = on_enabled
        self.on_protection_disabled = on_disabled
        
    def show(self):
        """
        Показывает окно.
        """
        self.deiconify()
        self.lift()
        self.focus_force()
        
        # Принудительное обновление и фокус
        self.update()
        self.focus_force()
        
        # Восстанавливаем из трея, если окно было скрыто
        if hasattr(self, 'tray_manager') and self.tray_manager:
            self.tray_manager.show_window()

    def hide(self):
        """
        Скрывает окно.
        """
        self.withdraw()
