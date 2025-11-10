"""
Модуль для работы с API market.csgo.com
"""
import requests
import time
from typing import Dict, List, Optional


class MarketAPI:
    """Клиент для работы с Market.CSGO API"""
    
    BASE_URL = "https://market.csgo.com/api/v2"
    
    def __init__(self, api_key: str):
        """
        Инициализация клиента API
        
        Args:
            api_key: API ключ для доступа к market.csgo.com
        """
        self.api_key = api_key
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, max_retries: int = 3) -> Dict:
        """
        Выполнить запрос к API с повторными попытками при ошибках
        
        Args:
            endpoint: Конечная точка API
            params: Дополнительные параметры запроса
            max_retries: Максимальное количество попыток
        
        Returns:
            Ответ API в виде словаря
        """
        if params is None:
            params = {}
        
        params['key'] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        retry_delay = 10  # секунд
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                # Отладка: выводим URL запроса для set-price
                if endpoint == "set-price":
                    print(f"[DEBUG] Полный URL запроса: {response.url}")
                
                response.raise_for_status()
                return response.json()
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                # Ошибки таймаута или соединения - пробуем еще раз
                if attempt < max_retries - 1:
                    print(f"⚠️  Ошибка соединения: {e}")
                    print(f"⏳ Жду {retry_delay} секунд перед повторной попыткой ({attempt + 2}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"❌ Ошибка при запросе к API после {max_retries} попыток: {e}")
                    return {"success": False, "error": str(e)}
                    
            except requests.exceptions.RequestException as e:
                # Другие ошибки (например, 404, 500) - не повторяем
                print(f"Ошибка при запросе к API: {e}")
                return {"success": False, "error": str(e)}
    
    def get_my_inventory(self) -> Dict:
        """
        Получить список предметов, доступных для продажи
        
        Returns:
            Словарь с информацией о предметах
        """
        return self._make_request("my-inventory")
    
    def get_items_on_sale(self) -> Dict:
        """
        Получить список предметов на продаже (только активные, не проданные)
        
        Returns:
            Словарь с предметами на продаже
        """
        # v=2 - использовать новую версию API
        # Получаем только предметы, которые активно продаются (status != 2)
        response = self._make_request("items", params={"v": "2"})
        
        # Фильтруем только активные предметы (не проданные)
        if response.get("success", False) and "items" in response:
            all_items = response["items"]
            print(f"[DEBUG] Всего предметов получено от API: {len(all_items)}")
            
            active_items = []
            sold_count = 0
            for item in all_items:
                status = item.get("status", 0)
                # status 2 = продано/в процессе продажи, пропускаем такие
                if status != 2:
                    active_items.append(item)
                else:
                    sold_count += 1
                    print(f"[DEBUG] Пропущен проданный предмет: {item.get('market_hash_name', 'Unknown')} (status={status})")
            
            print(f"[DEBUG] Активных предметов на продаже: {len(active_items)}")
            print(f"[DEBUG] Проданных/в процессе: {sold_count}")
            
            response["items"] = active_items
        
        return response
    
    def get_price_list(self, market_hash_name: str) -> Dict:
        """
        Получить список цен для конкретного предмета
        
        Args:
            market_hash_name: Название предмета на рынке
        
        Returns:
            Словарь с ценами
        """
        return self._make_request("search-item-by-hash-name", 
                                 params={"hash_name": market_hash_name})
    
    def get_best_offer_for_item(self, market_hash_name: str) -> Dict:
        """
        Получить лучшее предложение для конкретного предмета
        
        Args:
            market_hash_name: Название предмета на рынке
        
        Returns:
            Словарь с информацией о лучшем предложении
        """
        result = self._make_request("search-item-by-hash-name", 
                                    params={"hash_name": market_hash_name})
        return result
    
    def set_price(self, item_id: str, price: float, currency: str = "USD") -> Dict:
        """
        Установить цену для предмета
        
        Args:
            item_id: ID предмета
            price: Новая цена в долларах
            currency: Валюта (по умолчанию USD)
        
        Returns:
            Результат операции
        """
        # API market.csgo принимает цену умноженную на 1000 (как в search-item-by-hash-name)
        # Например: $114.391 -> 114391
        price_formatted = int(round(price * 1000))
        
        params = {
            "item_id": item_id,
            "price": price_formatted,
            "cur": currency
        }
        print(f"[DEBUG] Отправляем в set-price:")
        print(f"  - item_id: {item_id}")
        print(f"  - price (в долларах): ${price:.3f}")
        print(f"  - price (форматированная): {price_formatted}")
        print(f"  - currency: {currency}")
        
        return self._make_request("set-price", params=params)
    
    def ping(self) -> Dict:
        """
        Пинг для активации продаж (новая версия API)
        
        Returns:
            Результат операции
        """
        return self._make_request("ping-new", params={"v": "2"})
    
    def get_balance(self) -> Dict:
        """
        Получить баланс аккаунта
        
        Returns:
            Информация о балансе
        """
        return self._make_request("get-money")

