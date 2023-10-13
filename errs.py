import datetime
import json
import platform
import aiohttp
import aiofiles
import asyncio
from aiocsv import AsyncWriter
import math
import random
from m_headers import headers
# Заголовки общие:

current_time = datetime.datetime.now().strftime("%d.%m.%Y %H-%M")


async def get_products_magnit():
    # Создадим сессию:
    async with aiohttp.ClientSession() as session:
        response = await session.get('https://web-gateway.middle-api.magnit.ru/v1/cities', headers=headers)
        rest = await response.json()

        """Получим список Городов и выберем один из них"""
        list_city = []
        for item in rest['cities']:
            city = item['city']
        # Создадим список городов для вывода пользователю:
        list_city.append(city)
        for lst in enumerate(sorted(list_city), 1):
            cities = f"{lst[0]}. {lst[1]}"
        print(cities)
        while True:
            choice_city = input("[ENTER] Укажите Город (по аналогии из списка выше):\n")
            if choice_city in [item['city'] for item in rest['cities']]:
                for town in rest['cities']:
                    if choice_city == town['city']:
                        longitude = town['longitude']
                        latitude = town['latitude']

                        # Сделаем случайную паузу между сессиями:
                        await asyncio.sleep(random.randrange(1, 4))

                        """Получим список магазинов выбранного Города и выберем один изних"""
                        params = {
                            'Longitude': f"{longitude}",  # Долгота и широта Города
                            'Latitude': f"{latitude}",
                            'StoreType': 'MM',  # MM: Магнит у дома
                            'Radius': '20',
                            'Limit': '500',
                        }

                        response = await session.get(
                            'https://web-gateway.middle-api.magnit.ru / v1 / geolocation / store', params=params,
                            headers=headers)
                        rest = await response.json()

                        while True:
                            store_search = input(
                                "[SEARCH] Укажите улицу нахождения магазина (можно без окончания):\n ").lower()
                            list_stores = []
                            list_compare = [sel['address'].lower() for sel in rest['stores']]
                            if any(store_search in item for item in list_compare):
                                for shop in rest['stores']:
                                    address = shop['address'].replace(f"{choice_city} г, ", '').lower().strip()
                                    store_id = shop['id']
                                    work = f"{shop['openingHours']} - {shop['closingHours']}"

                                    # Создадим список расположения магазинов с указанием ID для вывода пользователю:
                                    if store_search in address:
                                        list_stores.append(
                                            f"{address} [{work}] ID: {store_id}"
                                        )
                                break
                            else:
                                print("[ERROR🔥] Такого слова нет в названиях улиц магазинов!")

                        # Сделаем нумерованный список с сортировкой для вывода пользователю:
                        for lst in enumerate(sorted(list_stores), 1):
                            stores = f"{lst[0]}. {lst[1]}"
                            print(stores)

                        """Загрузим все продукты по акциям, где есть цены, из выбранного
                        магазина"""
                        while True:
                            user_enter_id = input("[CHOOSE] Введите номер ID магазина из списка выше:\n ")
                            if any(user_enter_id in item for item in list_stores):
                                choice_store_id = user_enter_id
                                break
                            else:
                                print("[ERROR🔥] Нужно указать корректный ID!")

                        # Вернём магазин пользователя:
                        for part in list_stores:
                            if user_enter_id in part:
                                user_store = part[0:part.find(' ID')]
                        print(f"Магазин: {user_store}")
                        # Сначала получим кол-во карточек продуктов по акциям:

                        params = {
                            'offset': '0',  # 0 - первые 36 товаров (1 стр)
                            'limit': '36',
                            'storeId': f"{choice_store_id}",
                            'sortBy': 'priority',
                            'order': 'desc',
                            'adult': 'true',
                        }

                        response = await session.get('https://web-gateway.middle-api.magnit.ru / v1 / promotion',
                                                     params=params,
                                                     headers=headers)
                        rest = await response.json()
                        card_count = rest['total']
                        pages_count = math.ceil(card_count / len([x['categoryName'] for x in rest['data']]))
                        print(f"Total Pages: {pages_count}")

                        # Сделаем случайную паузу между сессиями:
                        await asyncio.sleep(random.randrange(1, 4))

                        # Далее загружаем каждую страницу и извлекаем данные:
                        count = 1
                        title_csv = [
                            ['name', 'category', 'price', 'end_promotion', 'image', 'link']
                        ]
                        list_products = []
                        for page in range(0, 108, 36):  # range(0, card_count, 36)
                            params = {
                                'offset': f"{page}",
                                'limit': '36',
                                'storeId': f"{choice_store_id}",
                                'sortBy': 'priority',
                                'order': 'desc',
                                'adult': 'true',
                            }

                        response = await session.get('https://web-gateway.middle-api.magnit.ru / v1 / promotions',
                                                     params=params,
                                                     headers=headers)
                        rest = await response.json()

                        for item in rest['data']:
                            # Если ключ Price есть в продукте, то извлекаем из него данные:
                            if 'price' in item:
                                name = item['name']
                                category = item['categoryName']
                                price = str(float(item['price']) / 100).replace('.', ',')
                                # Дату переформатируем в другую последовательность: d.m.y
                                end_date = datetime.datetime.strptime(item['endDate'], '%Y-%m-% d ').strftime(
                                    ' % d. % m. % y ')
                                image = item['imageUrl']
                                # Иногда отсутствует productCode продукта, который входит всостав ссылки:
                                try:
                                    link = 'https://magnit.ru/promo/' + item['productCode']
                                except KeyError:
                                    link = "[ERROR] Нет ссылки на карточку!"
                                list_products.append({
                                    'name': name,
                                    'category': category,
                                    'price': price,
                                    'end_promotion': end_date,
                                    'image': image,
                                    'link': link
                                })
                                data_csv = [name, category, price, end_date, image, link]
                                title_csv.append(data_csv)
                        print(f"[+] Page {count} of {pages_count}")
                        # Сделаем случайную паузу между сессиями:
                        await asyncio.sleep(random.randrange(1, 4))
                        count += 1
                        async with aiofiles.open(f"data-1/MagnitHome_{choice_city}.json", 'w',
                                                 encoding='utf-8') as file:
                            await file.write(json.dumps(list_products, indent=4, ensure_ascii=False))
                        async with aiofiles.open(f"data-1/MagnitHome_{choice_city}_{current_time}.csv", 'w',
                                                 newline='') as file:
                            writer = AsyncWriter(file, delimiter=";")
                            await writer.writerows(title_csv)

            break
        else:
            print("[ERROR🔥] Введите точное соответствие с заглавной буквы!")


async def main():
    await get_products_magnit()


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())