import aiohttp
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class GeckoTerminalAPI:
    BASE_URL = "https://api.geckoterminal.com/api/v2"
    
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_trending_ronin_pools(self) -> Dict:
        """Get trending pools for Ronin network."""
        endpoint = f"{self.BASE_URL}/networks/ronin/trending_pools"
        params = {
            "include": "base_token,quote_token,dex",
            "page": 1,
            "limit": 10
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Trending pools response: {data}")  # Debug log
                    return data
                else:
                    logger.error(f"Failed to get trending pools: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching trending pools: {str(e)}")
            return None

    async def get_ronin_pools(self, page: int = 1, limit: int = 20) -> Dict:
        """Get Ronin pools data."""
        endpoint = f"{self.BASE_URL}/networks/ronin/pools"
        params = {
            "page": page,
            "limit": limit,
            "include": "base_token,quote_token,dex"
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get Ronin pools: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching Ronin pools: {str(e)}")
            return None

    async def get_pool_info(self, pool_address: str) -> Dict:
        """Get detailed information about a specific pool."""
        endpoint = f"{self.BASE_URL}/networks/ronin/pools/{pool_address}"
        params = {
            "include": "base_token,quote_token,dex"
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get pool info: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching pool info: {str(e)}")
            return None

    async def search_pools(self, query: str) -> List[Dict]:
        """Search for pools by token name or symbol."""
        endpoint = f"{self.BASE_URL}/networks/ronin/pools/search"
        params = {
            "query": query,
            "include": "base_token,quote_token,dex"
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to search pools: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error searching pools: {str(e)}")
            return None

    async def get_token_pools(self, token_address: str) -> Dict:
        """Get pools that contain a specific token."""
        # Add ronin_ prefix if not present
        if not token_address.startswith('ronin_'):
            token_address = f'ronin_{token_address}'
            
        # For Ronin network, we need to use the address without the prefix in the URL
        endpoint_address = token_address.replace('ronin_', '')
        endpoint = f"{self.BASE_URL}/networks/ronin/tokens/{endpoint_address}/pools"
        params = {
            "include": "base_token,quote_token,dex",
            "page": 1,
            "limit": 10
        }
        
        try:
            logger.debug(f"Fetching token pools for {token_address} from endpoint: {endpoint}")
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Token pools response: {data}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get token pools: Status {response.status}, Response: {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching token pools: {str(e)}")
            return None 