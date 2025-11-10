"""
Модуль для управления ценами и перебивания
"""
import time
from typing import Dict, List, Optional, Tuple
from modules.api_client import MarketAPI
from modules.config_manager import ConfigManager


class ItemInfo:
    """Информация о предмете на продаже"""
    
    def __init__(self, item_id: str, market_hash_name: str, current_price: float, 
                 best_price: float, position: int):
        self.item_id = item_id
        self.market_hash_name = market_hash_name
        self.current_price = current_price
        self.best_price = best_price
        self.position = position
    
    def __repr__(self):
        return (f"ItemInfo(id={self.item_id}, name={self.market_hash_name}, "
                f"current_price=${self.current_price:.3f}, best_price=${self.best_price:.3f}, "
                f"position={self.position})")


class PriceManager:
    """Управление ценами и автоматическое перебивание"""
    
    def __init__(self, api: MarketAPI, config: ConfigManager):
        """
        Инициализация менеджера цен
        
        Args:
            api: Клиент API
            config: Менеджер конфигурации
        """
        self.api = api
        self.config = config
    
    def get_my_items_info(self) -> List[ItemInfo]:
        """
        Получить информацию о всех моих предметах на продаже
        
        Returns:
            Список с информацией о предметах
        """
        items_info = []
        
        # Получаем список предметов на продаже
        my_items_response = self.api.get_items_on_sale()
        
        if not my_items_response.get("success", False):
            print(f"Ошибка при получении списка предметов на продаже: {my_items_response.get('error', 'неизвестная ошибка')}")
            return items_info
        
        my_items = my_items_response.get("items", [])
        
        if not my_items:
            print("У вас нет предметов на продаже")
            return items_info
        
        print(f"Найдено {len(my_items)} предмет(ов) на продаже\n")
        
        # Обрабатываем каждый предмет
        for item in my_items:
            item_id = item.get("item_id", "")
            market_hash_name = item.get("market_hash_name", "")
            
            # Цена уже в долларах
            current_price = float(item.get("price", 0))
            
            # Получаем информацию о лучшей цене для этого предмета
            print(f"Запрашиваю цены для: {market_hash_name}...")
            price_info = self.api.get_best_offer_for_item(market_hash_name)
            
            if price_info.get("success", False) and price_info.get("data"):
                # Находим лучшую цену продажи (самую низкую) из списка предложений
                offers = price_info.get("data", [])
                
                if offers:
                    # Первое предложение - это лучшая цена продажи
                    raw_best_price = offers[0].get("price", 0)
                    # API search-item-by-hash-name возвращает цены умноженные на 1000
                    best_price = float(raw_best_price) / 1000
                    print(f"  ✓ Лучшая цена продажи: ${best_price:.3f}")
                else:
                    best_price = current_price
                    print(f"  ⚠️  Не найдены предложения на продажу")
            else:
                print(f"  ⚠️  Не удалось получить цены для {market_hash_name}")
                best_price = current_price
            
            # Определяем позицию
            position = self._calculate_position(current_price, best_price)
            
            # Выводим информацию о нашем предмете
            print(f"  Наша цена: ${current_price:.3f}")
            if position == 1:
                print(f"  Позиция: #{position} 🥇 (Лучшая цена!)")
            else:
                print(f"  Позиция: #{position} (не первый)")
            print()
            
            item_info = ItemInfo(
                item_id=item_id,
                market_hash_name=market_hash_name,
                current_price=current_price,
                best_price=best_price,
                position=position
            )
            
            items_info.append(item_info)
            
            # Небольшая задержка между запросами
            time.sleep(0.5)
        
        return items_info
    
    def _calculate_position(self, current_price: float, best_price: float) -> int:
        """
        Вычислить позицию предмета (1 = самый первый, 2+ = не первый)
        
        Args:
            current_price: Текущая цена предмета
            best_price: Лучшая цена на рынке
        
        Returns:
            Позиция предмета
        """
        # Если наша цена меньше или равна лучшей, мы первые
        # Используем небольшую погрешность для сравнения float чисел
        if current_price <= best_price:
            return 1
        else:
            # Примерная позиция (чем больше разница, тем дальше от первого места)
            # Каждый $0.01 разницы = примерно 1 позиция
            position_diff = int((current_price - best_price) / 0.01) + 1
            return max(2, position_diff)
    
    def should_update_price(self, item: ItemInfo) -> Tuple[bool, Optional[float]]:
        """
        Определить, нужно ли обновить цену для предмета
        
        Args:
            item: Информация о предмете
        
        Returns:
            Кортеж (нужно ли обновить, новая цена)
        """
        # Если мы уже первые, обновлять не нужно
        if item.position == 1:
            return False, None
        
        # Вычисляем новую цену (на $0.01 ниже лучшей)
        new_price = item.best_price - 0.01
        
        # Проверяем минимальную цену
        min_price = self.config.get_min_price(item.market_hash_name)
        
        if min_price is not None:
            if new_price < min_price:
                print(f"❌ {item.market_hash_name}: новая цена ${new_price:.3f} ниже минимальной ${min_price:.3f}")
                return False, None
        
        # Если новая цена такая же или выше текущей, не обновляем
        if new_price >= item.current_price:
            return False, None
        
        return True, new_price
    
    def update_item_price(self, item: ItemInfo, new_price: float, auto_confirm: bool = False) -> bool:
        """
        Обновить цену предмета
        
        Args:
            item: Информация о предмете
            new_price: Новая цена
            auto_confirm: Автоматическое подтверждение без запроса
        
        Returns:
            True если успешно, False если нет
        """
        print(f"\n🔄 Планируется обновить цену для {item.market_hash_name}:")
        print(f"   Текущая цена: ${item.current_price:.3f}")
        print(f"   Новая цена: ${new_price:.3f}")
        print(f"   Разница: ${item.current_price - new_price:.3f}")
        
        if not auto_confirm:
            confirm = input("\n⚠️  ВНИМАНИЕ! Продолжить? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y', 'да']:
                print("❌ Обновление отменено")
                return False
        
        # Пытаемся обновить цену с повторными попытками при ошибке "too_often"
        max_retries = 3
        retry_delay = 10  # секунд
        
        for attempt in range(max_retries):
            if attempt > 0:
                print(f"⏳ Попытка {attempt + 1}/{max_retries}...")
            
            response = self.api.set_price(item.item_id, new_price)
            
            if response.get("success", False):
                print(f"✅ Цена успешно обновлена на ${new_price:.3f}")
                print(f"⚠️  ПРОВЕРЬТЕ НА САЙТЕ, что цена установлена правильно!")
                return True
            
            error = response.get("error", "Неизвестная ошибка")
            
            # Если ошибка "too_often" и это не последняя попытка - ждем и пробуем снова
            if error == "too_often" and attempt < max_retries - 1:
                print(f"⚠️  Слишком частые запросы. Жду {retry_delay} секунд перед повторной попыткой...")
                time.sleep(retry_delay)
                continue
            
            # Для других ошибок или если это последняя попытка
            print(f"❌ Ошибка при обновлении цены: {error}")
            if attempt == max_retries - 1:
                print(f"❌ Превышено количество попыток ({max_retries})")
            print(f"[DEBUG] Полный ответ API: {response}")
            return False
        
        return False
    
    def process_all_items(self, auto_confirm: bool = False) -> Dict:
        """
        Обработать все предметы и обновить цены где необходимо
        
        Args:
            auto_confirm: Автоматическое подтверждение без запроса
        
        Returns:
            Статистика обработки
        """
        items = self.get_my_items_info()
        
        stats = {
            "total": len(items),
            "updated": 0,
            "skipped": 0,
            "first_position": 0,
            "below_min": 0
        }
        
        for item in items:
            if item.position == 1:
                stats["first_position"] += 1
                print(f"  ✓ {item.market_hash_name} - УЖЕ НА ПЕРВОМ МЕСТЕ")
                continue
            
            should_update, new_price = self.should_update_price(item)
            
            if should_update:
                if self.update_item_price(item, new_price, auto_confirm):
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            else:
                stats["skipped"] += 1
                min_price = self.config.get_min_price(item.market_hash_name)
                if min_price and (item.best_price - 0.01) < min_price:
                    stats["below_min"] += 1
        
        return stats

