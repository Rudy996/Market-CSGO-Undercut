"""
Главный модуль для автоматического перебивания цен на market.csgo.com
"""
import os
import sys
import time
from typing import Optional
from modules.api_client import MarketAPI
from modules.config_manager import ConfigManager
from modules.price_manager import PriceManager, ItemInfo


def clear_screen():
    """Очистить экран консоли"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Вывести заголовок программы"""
    print("=" * 80)
    print("Market.CSGO - Автоматическое перебивание цен".center(80))
    print("=" * 80)
    print()


def print_item_info(item: ItemInfo, index: int, config: ConfigManager):
    """
    Вывести информацию о предмете
    
    Args:
        item: Информация о предмете
        index: Номер предмета в списке
        config: Менеджер конфигурации
    """
    min_price = config.get_min_price(item.market_hash_name)
    min_price_str = f"${min_price:.3f}" if min_price is not None else "не установлена"
    
    position_icon = "🥇" if item.position == 1 else "📊"
    
    print(f"{position_icon} Предмет #{index + 1}")
    print(f"   Название: {item.market_hash_name}")
    print(f"   Текущая цена: ${item.current_price:.3f}")
    print(f"   Лучшая цена на рынке: ${item.best_price:.3f}")
    print(f"   Позиция: #{item.position}")
    print(f"   Минимальная цена: {min_price_str}")
    print("-" * 80)


def show_items_menu(price_manager: PriceManager, config: ConfigManager):
    """
    Показать меню с предметами
    
    Args:
        price_manager: Менеджер цен
        config: Менеджер конфигурации
    """
    clear_screen()
    print_header()
    
    print("🔄 Обновляю информацию о предметах с сервера...")
    items = price_manager.get_my_items_info()
    
    if not items:
        print("\n⚠️  У вас нет предметов на продаже\n")
        input("Нажмите Enter для продолжения...")
        return
    
    clear_screen()
    print_header()
    
    print(f"Всего предметов на продаже: {len(items)}\n")
    
    for i, item in enumerate(items):
        print_item_info(item, i, config)
    
    print("\nМеню:")
    print("1. Установить минимальную цену для предмета")
    print("2. Удалить минимальную цену для предмета")
    print("3. Обновить информацию")
    print("0. Назад")
    
    choice = input("\nВыберите действие: ").strip()
    
    if choice == "1":
        set_min_price_menu(items, config)
    elif choice == "2":
        remove_min_price_menu(items, config)
    elif choice == "3":
        show_items_menu(price_manager, config)
    elif choice == "0":
        return
    else:
        print("Неверный выбор")
        time.sleep(1)
        show_items_menu(price_manager, config)


def set_min_price_menu(items: list, config: ConfigManager):
    """
    Меню установки минимальной цены
    
    Args:
        items: Список предметов
        config: Менеджер конфигурации
    """
    print("\nВыберите предмет (введите номер):")
    
    for i, item in enumerate(items):
        print(f"{i + 1}. {item.market_hash_name}")
    
    choice = input("\nНомер предмета (0 - отмена): ").strip()
    
    try:
        index = int(choice) - 1
        if index == -1:
            return
        
        if 0 <= index < len(items):
            item = items[index]
            price_str = input(f"\nВведите минимальную цену для {item.market_hash_name} (USD): $").strip()
            
            try:
                price = float(price_str)
                if price > 0:
                    config.set_min_price(item.market_hash_name, price)
                    print("\n✅ Минимальная цена установлена")
                else:
                    print("\n❌ Цена должна быть больше 0")
            except ValueError:
                print("\n❌ Неверный формат цены")
        else:
            print("\n❌ Неверный номер предмета")
    except ValueError:
        print("\n❌ Введите число")
    
    time.sleep(2)


def remove_min_price_menu(items: list, config: ConfigManager):
    """
    Меню удаления минимальной цены
    
    Args:
        items: Список предметов
        config: Менеджер конфигурации
    """
    print("\nВыберите предмет (введите номер):")
    
    for i, item in enumerate(items):
        min_price = config.get_min_price(item.market_hash_name)
        if min_price is not None:
            print(f"{i + 1}. {item.market_hash_name} (мин: ${min_price:.3f})")
    
    choice = input("\nНомер предмета (0 - отмена): ").strip()
    
    try:
        index = int(choice) - 1
        if index == -1:
            return
        
        if 0 <= index < len(items):
            item = items[index]
            config.remove_min_price(item.market_hash_name)
            print("\n✅ Минимальная цена удалена")
        else:
            print("\n❌ Неверный номер предмета")
    except ValueError:
        print("\n❌ Введите число")
    
    time.sleep(2)


def auto_update_mode(price_manager: PriceManager, config: ConfigManager):
    """
    Режим автоматического обновления цен
    
    Args:
        price_manager: Менеджер цен
        config: Менеджер конфигурации
    """
    interval = config.get_check_interval()
    
    print(f"\n🤖 Автоматическое перебивание цен")
    print(f"⏱️  Интервал проверки: {interval} секунд")
    print(f"ℹ️  Нажмите Ctrl+C для остановки\n")
    
    confirm = input("Запустить? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y', 'да']:
        print("Отменено")
        return
    
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'='*80}")
            print(f"Итерация #{iteration} - {time.strftime('%H:%M:%S')}")
            print(f"{'='*80}\n")
            
            print("🔍 Проверяю предметы...")
            
            # Обрабатываем все предметы
            stats = price_manager.process_all_items(auto_confirm=True)
            
            print(f"\n📊 Статистика:")
            print(f"   Всего предметов: {stats['total']}")
            print(f"   На 1 месте: {stats['first_position']}")
            print(f"   Обновлено: {stats['updated']}")
            print(f"   Пропущено: {stats['skipped']}")
            print(f"   Ниже минимальной цены: {stats['below_min']}")
            
            print(f"\n⏳ Следующая проверка через {interval} секунд...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка автоматического режима...")


def show_settings_menu(config: ConfigManager):
    """
    Показать меню настроек
    
    Args:
        config: Менеджер конфигурации
    """
    clear_screen()
    print_header()
    
    interval = config.get_check_interval()
    
    print(f"Текущие настройки:\n")
    print(f"Интервал проверки: {interval} секунд\n")
    
    print("1. Изменить интервал проверки")
    print("0. Назад")
    
    choice = input("\nВыберите действие: ").strip()
    
    if choice == "1":
        try:
            new_interval = int(input("\nВведите новый интервал в секундах: ").strip())
            if new_interval > 0:
                config.config["check_interval"] = new_interval
                config._save_config(config.config)
                print(f"\n✅ Интервал изменен на {new_interval} секунд")
                time.sleep(2)
            else:
                print("\n❌ Интервал должен быть больше 0")
                time.sleep(2)
        except ValueError:
            print("\n❌ Неверный формат")
            time.sleep(2)
    elif choice == "0":
        return


def main():
    """Главная функция программы"""
    
    # Инициализация
    config = ConfigManager()
    api_key = config.get_api_key()
    
    if not api_key:
        print("❌ API ключ не найден в конфигурации")
        print("Пожалуйста, укажите API ключ в файле config.json")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    
    api = MarketAPI(api_key)
    price_manager = PriceManager(api, config)
    
    # Проверяем подключение
    print("🔌 Проверяю подключение к API...")
    balance_info = api.get_balance()
    
    if not balance_info.get("success", False):
        print(f"❌ Ошибка подключения к API: {balance_info.get('error', 'неизвестная ошибка')}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    
    balance = balance_info.get("money", 0)
    print(f"✅ Подключение успешно! Баланс: ${balance:.3f}\n")
    time.sleep(2)
    
    # Главное меню
    while True:
        clear_screen()
        print_header()
        
        print("Главное меню:\n")
        print("1. Просмотр предметов на продаже")
        print("2. Запустить автоматическое перебивание цен")
        print("3. Настройки")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == "1":
            show_items_menu(price_manager, config)
        elif choice == "2":
            auto_update_mode(price_manager, config)
        elif choice == "3":
            show_settings_menu(config)
        elif choice == "0":
            print("\n👋 До свидания!")
            break
        else:
            print("\n❌ Неверный выбор")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("\nНажмите Enter для выхода...")

