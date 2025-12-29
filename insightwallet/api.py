
import asyncio
import aiohttp
from toga import App


class InsightAPI:
    def __init__(self, app:App):
        
        self.app = app
        self.base_url = None
        self.timeout=aiohttp.ClientTimeout(total=15)

    async def _get(self, path: str):
        url = f"{self.base_url}{path}"
        try:
            import ssl
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession() as session:
                headers={'User-Agent': 'Mozilla/5.0'}
                async with session.get(url, headers=headers, timeout=self.timeout, ssl=ssl_context) as resp:
                    if resp.status != 200:
                        return None
                    return await resp.json()
        except asyncio.TimeoutError:
            print("API timeout:", url)
        except aiohttp.ClientError as e:
            print("API error:", e)
        return None
    
    
    async def get_utxos(self, address: str):
        blockbook_coins = {"ZEC", "YEC"}
        if self.app.coin in blockbook_coins:
            endpoint = f"/utxo/{address}"
        else:
            endpoint = f"/addr/{address}/utxo"
        return await self._get(endpoint)
    
    
    async def get_address(self, address: str):
        blockbook_coins = {"ZEC", "YEC"}
        if self.app.coin in blockbook_coins:
            endpoint = f"/address/{address}"
        else:
            endpoint = f"/addr/{address}"
        return await self._get(endpoint)
    
    
    async def get_transactions(self, address: str):
        blockbook_coins = {"ZEC", "YEC"}
        if self.app.coin in blockbook_coins:
            endpoint = f"/address/{address}/txs"
        else:
            endpoint = f"/txs/?address={address}"
        data = await self._get(endpoint)
        if not data:
            return []
        return data.get("txs", [])
    

    async def get_transaction(self, txid: str):
        return await self._get(f"/tx/{txid}")
    
    
    async def get_block_height(self) -> int | None:
        data = await self._get("/status")
        if not data:
            return None
        blocks = data.get("info", {}).get("blocks")
        if blocks is not None:
            return blocks
        if "backend" in data and "blocks" in data["backend"]:
            return data["backend"]["blocks"]
        if "blockbook" in data and "bestHeight" in data["blockbook"]:
            return data["blockbook"]["bestHeight"]
        return None


    async def broadcast_tx(self, raw_tx: str) -> tuple[bool, str | None]:
        blockbook_coins = {"ZEC", "YEC"}
        try:
            import ssl
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession() as session:
                headers = {'User-Agent': 'Mozilla/5.0'}

                if self.app.coin in blockbook_coins:
                    url = f"{self.base_url}/sendtx"
                    payload = {"hex": raw_tx}
                    async with session.post(url, headers=headers, json=payload, timeout=self.timeout, ssl=ssl_context) as resp:
                        data = await resp.json()
                        if resp.status == 200 and "result" in data:
                            return True, data["result"]
                        text = await resp.text()
                        return False, f"Node returned {resp.status}: {text}"
                else:
                    url = f"{self.base_url}/tx/send"
                    payload = {"rawtx": raw_tx}
                    async with session.post(url, headers=headers, json=payload, timeout=self.timeout, ssl=ssl_context) as resp:
                        text = await resp.text()
                        if resp.status == 200:
                            return True, None
                        return False, f"Node returned {resp.status}: {text}"

        except aiohttp.ClientError as e:
            return False, f"Network error: {e}"






