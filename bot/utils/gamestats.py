from config import tracker_network_api_key
from utils.exceptions import Forbidden, Unknown, NotFound, Unavailable, RateLimit, InvalidPlatform
import urllib.parse

async def apex_fetch(client, platform: str, username: str):
    if platform in ('origin', 'xbl', 'psn'):
        pass
    else:
        raise InvalidPlatform("Platform is not: origin, xbl or psn.")
    headers = {
        'TRN-Api-Key': tracker_network_api_key,
        'cache-control': "no-cache"
    }
    async with client.get(f"https://public-api.tracker.gg/v1/apex/standard/profile/{platform}/{urllib.parse.quote(username)}", headers=headers) as resp:
        if resp.status == 401:
            raise Forbidden("Invalid Authorization.")
        if resp.status == 500:
            raise Unknown()
        if resp.status == 503:
            raise Unavailable()
        if resp.status == 429:
            raise RateLimit()
        # Why can't you just return 404 here API and make my life easier.
        json = await resp.json()
        try:
            error = json["errors"]
            if error[0]["code"] == "CollectorResultStatus::NotFound":
                raise NotFound()
        except KeyError:
            pass
        if resp.status == 200:
            return await resp.json()
        else:
            raise Unknown()
