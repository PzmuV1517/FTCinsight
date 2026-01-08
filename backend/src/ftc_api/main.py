import os
from typing import Any, Optional, Tuple, Union

from requests import Session  # type: ignore[import-untyped]

from src.ftc_api.constants import FTC_API_BASE_URL, get_auth_header
from src.ftc_api.utils import dump_cache, load_cache

# FTC Events API v2.0 endpoint
API_VERSION = "v2.0"
read_prefix = f"{FTC_API_BASE_URL}/{API_VERSION}/"

session = Session()


def _get_ftc(
    url: str, etag: Optional[str] = None
) -> Tuple[Union[Any, bool], Optional[str]]:
    """
    Make a request to the FTC Events API
    
    The FTC Events API uses Basic authentication with Base64 encoded credentials.
    """
    headers = {
        "Authorization": get_auth_header(),
        "Accept": "application/json",
    }
    
    if etag is not None:
        headers["If-Modified-Since"] = etag
        response = session.get(read_prefix + url, headers=headers)
        if response.status_code == 304:
            return True, etag
        elif response.status_code == 200:
            return response.json(), response.headers.get("Last-Modified")
    else:
        response = session.get(read_prefix + url, headers=headers)
        if response.status_code == 200:
            return response.json(), response.headers.get("Last-Modified")
        elif response.status_code == 401:
            raise ValueError("FTC API authentication failed. Check your credentials.")
        elif response.status_code == 404:
            return None, None
            
    return False, None


def get_ftc(
    url: str, etag: Optional[str] = None, cache: bool = True
) -> Tuple[Union[Any, bool], Optional[str]]:
    """
    Get data from FTC Events API with caching support
    """
    cache_path = "cache/ftc/" + url.replace("/", "_").replace("?", "_")
    
    if cache and os.path.exists(cache_path + "/data.p"):
        # Cache Hit
        return load_cache(cache_path), None

    data, new_etag = _get_ftc(url, etag)

    # Either Etag or Invalid
    if type(data) is bool:
        return data, new_etag

    # Null response
    if data is None:
        return False, None

    # Cache Miss - save to cache
    dump_cache(cache_path, data)
    return data, new_etag
