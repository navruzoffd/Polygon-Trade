from typing import Optional
import asyncio
import aiofiles
import json
from datetime import datetime
from playwright.async_api import Playwright
from logger import logger
from src.browser import Browser

class TradeBot(Browser):

    def __init__(self,
                 playwright: Playwright,
                 storage: Optional[str],
                 price_range: Optional[int]):

        super().__init__(playwright, storage)
        self.price_range = price_range

    async def collect_items_to_json(self, usd_rub: int, usd_token: int, price_mode:  Optional[str]):
        await self.page.wait_for_selector(".inventory_left_content")

        if price_mode:
            await self.page.click(".nice-select.sortprice")
            await self.page.locator(
                f"div.nice-select.sortprice.open ul.list li[data-value='{price_mode}']"
            ).click()

        await self.page.wait_for_selector(".inventory_left_content")

        items = await self.page.query_selector_all(".inventory_item.instant_item")
        logger.debug("items loaded")

        data = {
            "timeSync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "itemsCount": 0,
            "itemsList": []
        }


        for item in items:
            gun_name = await item.query_selector(".inventory_item_label")
            skin_name = await item.query_selector(".inventory_item_name")
            state = await item.query_selector(".inventory_item_category")
            price = await item.query_selector(".inventory_item_cost")
            
            if price:
                price = round(int(await price.inner_text())/usd_token*usd_rub, 2)

            data["itemsList"].append({
                "gun_name": await gun_name.inner_text() if gun_name else None,
                "skin_name": await skin_name.inner_text() if skin_name else None,
                "state": await state.inner_text() if state else None,
                "priceRub": price if price else None
            })

        data["itemsCount"] = len(data["itemsList"])

        json_data = json.dumps(data, ensure_ascii=False, indent=4)

        # Сохранение в файл
        async with aiofiles.open("result.json", 'w', encoding='utf-8') as f:
            await f.write(json_data)

        logger.info("JSON form loaded")

    async def auth(self):
        await self._init_browser()
        self.page = await self.context.new_page()
        await self.page.goto("https://plgeubet.com/")
        await self.page.click(".guest")
        await self.page.click(".window_steam_button")
        await self.page.wait_for_url("https://plgeubet.com/")
        await self.context.storage_state(path="storage.json")
        logger.info("account saved")
        await self.browser.close()

    async def steam_compare(self):
        with open('result.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        items = data["itemsList"]
        await self.page.goto("https://steamcommunity.com/market/search?appid=730")
        await self.page.wait_for_load_state("load")

        for i in range(data["itemsCount"]):
            search_name = f'{items[i]["gun_name"]} {items[i]["skin_name"]} {items[i]["state"]}'

            await self.page.fill("#findItemsSearchBox", search_name)
            await self.page.press("#findItemsSearchBox", "Enter")
            await self.page.wait_for_load_state("load")

            while not await self.page.query_selector(".market_listing_table_header"):
                await self.page.reload()
                await self.page.wait_for_load_state("load")

            price = await self.page.locator(".market_table_value .normal_price").first.inner_text()
            price = float(price.replace("руб.", "").strip().replace(",", "."))
            benefit = round(price * 0.87 / items[i]["priceRub"] - 1, 2)*100 
            print(f'{items[i]["skin_name"]} = {benefit}%')
