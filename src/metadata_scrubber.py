"""
Модуль для очистки метаданных из файлов.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional, List
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import logging

logger = logging.getLogger(__name__)


class MetadataScrubber:
    """
    Класс для очистки метаданных из файлов.
    """

    def __init__(self):
        self.cleaned_files = 0
        self.removed_geotags = 0
        self.removed_device_info = 0
        self.removed_software_info = 0
        self.removed_personal_info = 0
        self.last_action = ""
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.mp4', '.avi', '.mov', '.mkv', '.pdf', '.docx']
        
        # Категории метаданных для удаления
        self.metadata_categories = {
            'location': self._is_gps_tag,
            'device_info': self._is_device_tag,
            'software': self._is_software_tag,
            'personal': self._is_personal_tag
        }

    def _is_gps_tag(self, tag: str) -> bool:
        """
        Проверяет, является ли тег GPS-координатами.

        Args:
            tag: Имя тега

        Returns:
            True, если тег связан с GPS
        """
        gps_tags = ['GPSInfo', 'GPSLatitude', 'GPSLongitude', 'GPSAltitude', 
                   'GPSTimeStamp', 'GPSSpeed', 'GPSDestLatitude', 'GPSDestLongitude']
        return any(gps_tag.lower() in str(tag).lower() for gps_tag in gps_tags)

    def _is_device_tag(self, tag: str) -> bool:
        """
        Проверяет, является ли тег информацией об устройстве.

        Args:
            tag: Имя тега

        Returns:
            True, если тег связан с устройством
        """
        device_tags = ['Make', 'Model', 'LensModel', 'SerialNumber', 
                      'Hardware', 'Firmware', 'Software']
        return any(device_tag.lower() in str(tag).lower() for device_tag in device_tags)

    def _is_software_tag(self, tag: str) -> bool:
        """
        Проверяет, является ли тег информацией о программном обеспечении.

        Args:
            tag: Имя тега

        Returns:
            True, если тег связан с ПО
        """
        software_tags = ['Software', 'Application', 'Creator', 'EditHistory', 
                        'History', 'Processing', 'Filter']
        return any(software_tag.lower() in str(tag).lower() for software_tag in software_tags)

    def _is_personal_tag(self, tag: str) -> bool:
        """
        Проверяет, является ли тег персональной информацией.

        Args:
            tag: Имя тега

        Returns:
            True, если тег содержит персональные данные
        """
        personal_tags = ['Artist', 'Author', 'Creator', 'Copyright', 'Comment', 
                        'Description', 'Title', 'Subject', 'Keywords', 'Rating']
        return any(personal_tag.lower() in str(tag).lower() for personal_tag in personal_tags)

    def _get_file_metadata(self, file_path: Path) -> Dict:
        """
        Извлекает метаданные из файла.

        Args:
            file_path: Путь к файлу

        Returns:
            Словарь с метаданными
        """
        metadata = {}
        
        try:
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.tiff']:
                with Image.open(file_path) as img:
                    exif_data = img.getexif()
                    
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            metadata[str(tag)] = str(value)
            
        except Exception as e:
            logger.warning(f"Не удалось извлечь метаданные из {file_path}: {e}")
            
        return metadata

    def _has_metadata(self, file_path: Path) -> bool:
        """
        Проверяет, содержит ли файл метаданные.

        Args:
            file_path: Путь к файлу

        Returns:
            True, если файл содержит метаданные
        """
        metadata = self._get_file_metadata(file_path)
        return len(metadata) > 0

    def _remove_metadata_from_image(self, file_path: Path, categories_to_remove: List[str]) -> bool:
        """
        Удаляет метаданные из изображения.

        Args:
            file_path: Путь к файлу
            categories_to_remove: Список категорий метаданных для удаления

        Returns:
            True, если очистка прошла успешно
        """
        try:
            # Открываем изображение
            with Image.open(file_path) as img:
                # Создаем копию изображения без EXIF данных
                data = list(img.getdata())
                image_without_exif = Image.new(img.mode, img.size)
                image_without_exif.putdata(data)
                
                # Сохраняем изображение без метаданных
                # Определяем формат по расширению
                format_map = {
                    '.jpg': 'JPEG',
                    '.jpeg': 'JPEG',
                    '.png': 'PNG',
                    '.tiff': 'TIFF',
                    '.bmp': 'BMP',
                    '.gif': 'GIF'
                }
                
                format_name = format_map.get(file_path.suffix.lower())
                
                if format_name:
                    # Создаем временный файл
                    temp_path = file_path.with_suffix(file_path.suffix + '.temp')
                    temp_created = False
                    try:
                        # Сохраняем временный файл
                        image_without_exif.save(temp_path, format=format_name)
                        temp_created = True
                        
                        # Заменяем оригинальный файл
                        shutil.move(str(temp_path), str(file_path))
                        
                        # Обновляем статистику
                        self.cleaned_files += 1
                        self.last_action = file_path.name
                        
                        # Обновляем статистику по категориям
                        original_metadata = self._get_file_metadata(file_path)
                        for tag in original_metadata:
                            if self._is_gps_tag(tag) and 'location' in categories_to_remove:
                                self.removed_geotags += 1
                            elif self._is_device_tag(tag) and 'device_info' in categories_to_remove:
                                self.removed_device_info += 1
                            elif self._is_software_tag(tag) and 'software' in categories_to_remove:
                                self.removed_software_info += 1
                            elif self._is_personal_tag(tag) and 'personal' in categories_to_remove:
                                self.removed_personal_info += 1
                        
                        logger.info(f"Метаданные удалены из {file_path}")
                        return True
                    
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении временного файла или замене оригинала: {e}")
                        return False
                        
                    finally:
                        # Удаляем временный файл, если он был создан
                        if temp_created and temp_path.exists():
                            try:
                                os.unlink(temp_path)
                            except Exception as e:
                                logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}")
                else:
                    logger.error(f"Неподдерживаемый формат изображения: {file_path.suffix}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при удалении метаданных из {file_path}: {e}")
            return False

    def scrub_file(self, file_path: str, categories_to_remove: Optional[List[str]] = None) -> bool:
        """
        Очищает метаданные из указанного файла.

        Args:
            file_path: Путь к файлу для обработки
            categories_to_remove: Список категорий метаданных для удаления

        Returns:
            True, если очистка прошла успешно, иначе False
        """
        file_path_obj = Path(file_path)
        
        # Проверяем существование файла
        if not file_path_obj.exists():
            logger.error(f"Файл не найден: {file_path}")
            return False
            
        # Проверяем поддерживаемый формат
        if file_path_obj.suffix.lower() not in self.supported_formats:
            logger.warning(f"Неподдерживаемый формат файла: {file_path_obj.suffix}")
            return False
            
        # Проверяем, содержит ли файл метаданные
        if not self._has_metadata(file_path_obj):
            logger.info(f"Файл не содержит метаданных: {file_path}")
            self.last_action = file_path_obj.name
            return True
        
        # Устанавливаем категории для удаления (все, если не указаны)
        if categories_to_remove is None:
            categories_to_remove = list(self.metadata_categories.keys())
        
        # Проверяем валидность категорий
        valid_categories = [cat for cat in categories_to_remove if cat in self.metadata_categories]
        if not valid_categories:
            logger.warning(f"Нет валидных категорий для удаления: {categories_to_remove}")
            return False
        
        # Очищаем метаданные в зависимости от типа файла
        if file_path_obj.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            return self._remove_metadata_from_image(file_path_obj, valid_categories)
        else:
            # Для других форматов можно добавить дополнительную логику
            logger.warning(f"Поддержка формата {file_path_obj.suffix} в разработке")
            return False

    def get_statistics(self) -> Dict:
        """
        Возвращает статистику по очистке метаданных.

        Returns:
            Словарь со статистикой
        """
        return {
            "cleaned_files": self.cleaned_files,
            "removed_geotags": self.removed_geotags,
            "removed_device_info": self.removed_device_info,
            "removed_software_info": self.removed_software_info,
            "removed_personal_info": self.removed_personal_info,
            "last_action": self.last_action
        }
        
    def reset_statistics(self):
        """
        Сбрасывает статистику.
        """
        self.cleaned_files = 0
        self.removed_geotags = 0
        self.removed_device_info = 0
        self.removed_software_info = 0
        self.removed_personal_info = 0
        self.last_action = ""