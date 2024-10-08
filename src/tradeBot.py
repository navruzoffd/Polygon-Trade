from typing import Optional
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

    async def collect_items_to_json(self, usd_rub: int, usd_token: int):
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
