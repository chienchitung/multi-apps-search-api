import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppInfo(BaseModel):
    name: Optional[str] = None
    link: Optional[str] = None
    platform: str = ""
    search_term: str = ""
    found: bool = False

class AppSearchManager:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    async def search_apple_store(self, session: aiohttp.ClientSession, search_term: str) -> AppInfo:
        base_url = f"https://www.apple.com/tw/search/{search_term}?src=serp"
        app_info = AppInfo(platform="Apple App Store", search_term=search_term)

        try:
            async with session.get(base_url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    if product_block := soup.find('div', class_='rf-serp-product-description'):
                        if name_tag := product_block.find('h2', class_='rf-serp-productname'):
                            app_info.name = name_tag.get_text(strip=True)
                            app_info.found = True
                        if link_tag := product_block.find('a', href=True):
                            app_info.link = link_tag['href']
                else:
                    logger.warning(f"Apple Store returned status {response.status} for term '{search_term}'")
        except Exception as e:
            logger.error(f"Apple Store search error for term '{search_term}': {e}")

        return app_info

    async def search_google_play(self, session: aiohttp.ClientSession, search_term: str) -> AppInfo:
        base_url = f"https://play.google.com/store/search?q={search_term}&c=apps&gl=TW&hl=zh_TW"
        app_info = AppInfo(platform="Google Play Store", search_term=search_term)

        try:
            async with session.get(base_url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    if name_div := soup.select_one('div.vWM94c'):
                        app_name = name_div.text.strip()
                        if app_name:
                            app_info.name = app_name
                            if link_element := soup.select_one('a[href*="/store/apps/details"]'):
                                app_info.link = f"https://play.google.com{link_element['href']}&hl=zh_TW"
                                app_info.found = True
                    else:
                        if name_div := soup.select_one('div.ubGTjb'):
                            app_name = name_div.text.strip()
                            if app_name:
                                app_info.name = app_name
                                if link_element := soup.select_one('a[href*="/store/apps/details"]'):
                                    app_info.link = f"https://play.google.com{link_element['href']}&hl=zh_TW"
                                    app_info.found = True

                else:
                    logger.warning(f"Google Play returned status {response.status} for term '{search_term}'")
        except Exception as e:
            logger.error(f"Google Play search error for term '{search_term}': {e}")

        return app_info

    async def search_all_platforms(self, search_terms: List[str]) -> List[Dict]:
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for term in search_terms:
                tasks.append(self.search_apple_store(session, term))
                tasks.append(self.search_google_play(session, term))
            
            search_results = await asyncio.gather(*tasks)
            results = [result.dict() for result in search_results]

        return results 