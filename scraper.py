import asyncio
import aiohttp
from aiohttp import ClientConnectorError
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time
import random

# concurrency controls
FETCH_SEMAPHORE = 20
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5
SEMAPHORE = asyncio.Semaphore(FETCH_SEMAPHORE)

# rotating user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5)"
]


async def fetch(session: aiohttp.ClientSession, url: str):
    """Fetch page text with retries, concurrency control, and jitter."""
    async with SEMAPHORE:
        delay = 1.0
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                async with session.get(url, headers=headers, timeout=REQUEST_TIMEOUT) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    else:
                        if resp.status in (403, 404):
                            print(f"❌ {url} does not exist (status {resp.status})")
                            return None
                        print(f"⚠️ {url} returned status {resp.status}, retrying…")
            except (asyncio.TimeoutError, ClientConnectorError, aiohttp.ClientError) as e:
                print(f"Attempt {attempt} failed for {url}: {e}")

            if attempt < MAX_RETRIES:
                await asyncio.sleep(delay)
                delay *= RETRY_BACKOFF

        return None


async def scrape_directory(session, url, visited, vlock):
    """Scrape a directory recursively (async)."""
    async with vlock:
        if url in visited:
            return {}
        visited.add(url)

    result = {"url": url, "folders": {}, "files": []}
    html = await fetch(session, url)
    if not html:
        return result

    soup = BeautifulSoup(html, "html.parser")
    folder_tasks = []

    for a in soup.find_all("a"):
        href = a.get("href")
        if not href or href.startswith("?") or href.startswith("#") or href == "../":
            continue

        full_url = urljoin(url, href)
        if href.endswith("/"):
            task = asyncio.create_task(scrape_directory(session, full_url, visited, vlock))
            folder_tasks.append((href, full_url, task))
            result["folders"][href] = None
        else:
            result["files"].append(full_url)

    if folder_tasks:
        subresults = await asyncio.gather(*[t for (_, _, t) in folder_tasks], return_exceptions=True)
        for (href, full_url, _), subres in zip(folder_tasks, subresults):
            if isinstance(subres, Exception):
                print(f"❌ Error scraping {full_url}: {subres}")
                result["folders"][href] = {}
            else:
                result["folders"][href] = subres

    await asyncio.sleep(random.uniform(0.1, 0.5))

    return result


async def scrape_all_roots():
    connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
    headers = {"Accept-Encoding": "gzip, deflate"}

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = []
        for i in range(1, 31):
            root_url = f"https://dl{i}.sermoviedown.pw/"
            visited = set()
            vlock = asyncio.Lock()
            tasks.append((root_url, scrape_directory(session, root_url, visited, vlock)))

        results_list = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        results = {}
        for (root_url, _), res in zip(tasks, results_list):
            if isinstance(res, Exception):
                print(f"❌ Failed at {root_url}: {res}")
            elif res and (res.get("folders") or res.get("files")):
                results[root_url] = res
            else:
                print(f"⚠️ Skipping empty result for {root_url}")

    return results


async def main():
    results = await scrape_all_roots()
    with open("all_directory_structures.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("✅ Done. Saved to all_directory_structures.json")


if __name__ == "__main__":
    asyncio.run(main())
