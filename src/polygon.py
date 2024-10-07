from typing import Optional
from playwright.async_api import Playwright
from logger import logger
from src.browser import Browser

class Polygon(Browser):

    def __init__(self,
                 playwright: Playwright,
                 storage: Optional[str],
                 price_range: Optional[int]):

        super().__init__(playwright, storage)
        self.price_range = price_range

    async def collect_items_to_json(self):
        await self.page.wait_for_selector(".inventory_item")
        logger.debug("Items loaded")
        # items = await self.page.query_selector_all("")
