from typing import Optional
from fake_useragent import UserAgent
import urllib.parse
from aiohttp import ClientSession
from playwright.async_api import Playwright
import aiofiles
import asyncio
import json
from datetime import datetime
from logger import logger
from src.browser import Browser

ua = UserAgent()

class TradeBot(Browser):

    def __init__(self,
                 playwright: Playwright,
                 storage: Optional[str],
                 usd_rub: float,
                 usd_token: int):
        super().__init__(playwright, storage)
        self.usd_rub = usd_rub
        self.usd_token = usd_token

    async def collect_items_to_json(self,
                                    price_mode:  Optional[str],
                                    quantity: int):
        await self.page.wait_for_selector(".inventory_left_content")

        if price_mode:
            await self.page.click(".nice-select.sortprice")
            await self.page.click(f"li[data-value='{price_mode}']")
            await self.page.wait_for_selector(".inventory_left_content")

        pages = int(quantity / 50)

        if pages > 0:
            for _ in range(pages):
                await self.page.click("text='load more'")
                await asyncio.sleep(3)

        items = await self.page.query_selector_all(".inventory_item.instant_item")
        logger.debug("items loaded")

        data = {
            "timeSync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "itemsCount": 0,
            "itemsList": []
        }

        for item in items[:quantity]:
            prefix = await item.query_selector(".inventory_item_prefix")
            gun_name = await item.query_selector(".inventory_item_label")
            skin_name = await item.query_selector(".inventory_item_name")
            state = await item.query_selector(".inventory_item_category")
            price = await item.query_selector(".inventory_item_cost")
            
            if price:
                price = round(int(await price.inner_text())/self.usd_token*self.usd_rub, 2)

            data["itemsList"].append({
                "prefix": (await prefix.inner_text() + "™") if prefix and await prefix.inner_text() else None,
                "gun_name": await gun_name.inner_text() if gun_name and await gun_name.inner_text() else None,
                "skin_name": await skin_name.inner_text() if skin_name and await skin_name.inner_text() else None,
                "state": await state.inner_text() if state and await state.inner_text() else None,
                "priceRub": price if price else None
            })

        data["itemsCount"] = len(data["itemsList"])

        json_data = json.dumps(data, ensure_ascii=False, indent=4)

        async with aiofiles.open("result.json", 'w', encoding='utf-8') as f:
            await f.write(json_data)

        logger.info("JSON file filled")

    async def auth(self):
        await self._init_browser()
        self.page = await self.context.new_page()
        await self.page.goto("https://plgeubet.com/")
        await self.page.click(".guest")
        await self.page.click(".window_steam_button")
        await self.page.wait_for_url("https://plgeubet.com/")
        await self.context.storage_state(path="storage.json")
        await self.browser.close()
        logger.info("account saved")

    async def steam_compare(self):
        with open('result.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        items = data["itemsList"]
        await self.page.goto("https://steamcommunity.com/market/search?appid=730")
        await self.page.wait_for_load_state("load")
        results = []
        counter = 0

        for i in range(data["itemsCount"]):
            item_name = " ".join(filter(None, [items[i]["prefix"], items[i]["gun_name"], items[i]["skin_name"], items[i]["state"]]))

            await self.page.fill("#findItemsSearchBox", item_name)
            await self.page.press("#findItemsSearchBox", "Enter")
            await self.page.wait_for_selector(".market_search_results_header")

            while not await self.page.query_selector(".market_listing_table_header"):
                await self.page.reload()
                await self.page.wait_for_selector(".market_search_results_header")

            price_str = await self.page.locator(".market_table_value .normal_price").first.inner_text()
            price = float(price_str.replace("руб.", "").strip().replace(",", "."))
            benefit = round((price * 0.87 / items[i]["priceRub"] - 1) * 100, 2)

            results.append({
                "name": item_name,
                "price": price,
                "benefit": benefit
            })

            counter += 1
            logger.info(f"[{counter}] {item_name} ({benefit}%)")

        sorted_results = sorted(results, key=lambda x: x['benefit'], reverse=True)
        print("\n---Sorted result---")
        for result in sorted_results:
                    print(f"{result['name']} = {result['price']} rub., Benefit: {result['benefit']}%")

    async def steam_compare_aiohttp(self):
        await self.browser.close()
        with open('result.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        items = data["itemsList"]
        exception_name = ["Case", "Souvenir Package"]
        results = []
        counter = 1 
        for i in range(data["itemsCount"]):
            prefix = items[i].get("prefix", "")
            gun_name = items[i].get("gun_name", "")
            skin_name = items[i].get("skin_name", "")
            state = items[i].get("state", "")

            if gun_name in exception_name:
                item_name = f"{skin_name} {gun_name}"
            else:
                item_name = " ".join(filter(None, [prefix, gun_name]))  # Префикс и название оружия
                if skin_name:
                    item_name += f" | {skin_name}"  # Добавляем пайплайн и название скина, если оно есть
                if state:
                    item_name += f" ({state})"  # Добавляем состояние в скобках, если оно есть

            hash_name = urllib.parse.quote(item_name)
            url = f"https://steamcommunity.com/market/priceoverview/?currency=5&appid=730&market_hash_name={hash_name}"
            headers = {"User-Agent": ua.random}
            async with ClientSession() as session:
                response = await session.get(url, headers=headers)
                status_code = response.status

                if status_code == 200:
                    response_json = await response.json()
                    price_str = response_json["lowest_price"]
                    price = float(price_str.replace("руб.", "").strip().replace(",", "."))
                    benefit = round((price * 0.87 / items[i]["priceRub"] - 1) * 100, 2)

                    results.append({
                        "name": item_name,
                        "price": price,
                        "benefit": benefit
                    })

                    logger.info(f"[{counter}] {item_name} ({benefit}%)")

                elif status_code == 500:
                    pass

                elif status_code == 429:
                    while response.status != 200:
                        await asyncio.sleep(7)
                        response = await session.get(url, headers=headers)
                else:
                    print(url)


                logger.debug(response.status)
                await asyncio.sleep(3)

            counter += 1

        sorted_results = sorted(results, key=lambda x: x['benefit'], reverse=True)
        print("\n---Sorted result---")
        for result in sorted_results:
                    print(f"{result['name']} = {result['price']} rub., Benefit: {result['benefit']}%")
