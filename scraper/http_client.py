import httpx

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def make_client(timeout: float = 30.0) -> httpx.AsyncClient:
    """Return an AsyncClient with a browser User-Agent and redirect following."""
    return httpx.AsyncClient(
        headers={"User-Agent": BROWSER_UA},
        follow_redirects=True,
        timeout=timeout,
    )
