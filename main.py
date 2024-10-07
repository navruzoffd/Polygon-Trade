from playwright.async_api import async_playwright
import asyncio 
from src.polygon import Polygon

async def main():
    async with async_playwright() as playwright:
        playwright = Polygon(playwright=playwright,
                            storage=None,
                            price_range=None)
        await playwright.start("https://plgeubet.com/withdraw/csgo_instant")
        await playwright.collect_items_to_json()
        await asyncio.sleep(3000)
if __name__ == "__main__":
    asyncio.run(main())
