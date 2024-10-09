from playwright.async_api import async_playwright
import asyncio 
from src.tradeBot import TradeBot
import os

async def main():
    async with async_playwright() as playwright:
        bot = TradeBot(playwright=playwright,
                       storage="storage.json" if os.path.isfile("storage.json") else None)
        # await bot.auth()
        await bot.start("https://plgeubet.com/withdraw/csgo_instant")
        await bot.collect_items_to_json(usd_rub=97,
                                        usd_token=1350,
                                        price_mode="0#5000",
                                        quantity=300)
        await bot.steam_compare()
        await asyncio.sleep(3000)




if __name__ == "__main__":
    asyncio.run(main())
