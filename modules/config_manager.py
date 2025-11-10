"""
Модуль для управления конфигурацией и минимальными ценами
"""
import json
import os
from typing import Dict, Optional


class ConfigManager:
    """Управление конфигурацией приложения"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Инициализация менеджера конфигурации
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """
        Загрузить конфигурацию из файла
        
        Returns:
            Словарь с конфигурацией
        """
        if not os.path.exists(self.config_path):
            # Создать конфигурацию по умолчанию
            default_config = {
                "api_key": "",
                "check_interval": 30,
                "min_prices": {}
            }
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке конфигурации: {e}")
            return {}
    
    def _save_config(self, config: Dict) -> None:
        """
        Сохранить конфигурацию в файл
        
        Args:
            config: Словарь с конфигурацией
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении конфигурации: {e}")
    
    def get_api_key(self) -> str:
        """
        Получить API ключ
        
        Returns:
            API ключ
        """
        return self.config.get("api_key", "")
    
    def get_check_interval(self) -> int:
        """
        Получить интервал проверки (в секундах)
        
        Returns:
            Интервал проверки
        """
        return self.config.get("check_interval", 30)
    
    def get_min_price(self, market_hash_name: str) -> Optional[float]:
        """
        Получить минимальную цену для предмета
        
        Args:
            market_hash_name: Название предмета на рынке
        
        Returns:
            Минимальная цена или None, если не установлена
        """
        min_prices = self.config.get("min_prices", {})
        return min_prices.get(market_hash_name)
    
    def set_min_price(self, market_hash_name: str, price: float) -> None:
        """
        Установить минимальную цену для предмета
        
        Args:
            market_hash_name: Название предмета на рынке
            price: Минимальная цена
        """
        if "min_prices" not in self.config:
            self.config["min_prices"] = {}
        
        self.config["min_prices"][market_hash_name] = price
        self._save_config(self.config)
        print(f"Минимальная цена для '{market_hash_name}' установлена: ${price:.2f}")
    
    def remove_min_price(self, market_hash_name: str) -> None:
        """
        Удалить минимальную цену для предмета
        
        Args:
            market_hash_name: Название предмета на рынке
        """
        if "min_prices" in self.config and market_hash_name in self.config["min_prices"]:
            del self.config["min_prices"][market_hash_name]
            self._save_config(self.config)
            print(f"Минимальная цена для '{market_hash_name}' удалена")
    
    def get_all_min_prices(self) -> Dict[str, float]:
        """
        Получить все установленные минимальные цены
        
        Returns:
            Словарь с минимальными ценами
        """
        return self.config.get("min_prices", {})

