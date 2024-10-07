from typing import Optional
from playwright.async_api import Playwright
from logger import logger

class Browser:

    def __init__(self,
                 playwright: Playwright,
                 storage: Optional[str]):
        self.playwright = playwright
        self.storage = storage

    async def _init_browser(self):
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled'
                ])
            
            self.context = await self.browser.new_context(
                storage_state=self.storage
            )
            logger.debug("browser initialized")

    async def start(self, url: str):
        await self._init_browser()
        self.page = await self.context.new_page()
        await self.page.goto(url)
        await self.page.wait_for_load_state('load')
        logger.debug("page loaded")

