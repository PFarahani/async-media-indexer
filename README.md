# Async Media Indexer

<img src="./assets/logo.png" alt="Logo" width="500"/>

Async Media Indexer is a Python tool for asynchronously crawling and indexing open media directories.  
It recursively collects directory structures and stores them in a structured JSON format for further analysis.
A GitHub action runs once a day and updates the output file; so you can always access the latest file in the repo.

## Features
- ⚡ Fully asynchronous (powered by `asyncio` and `aiohttp`)
- 🎯 Recursive directory scraping
- 🔄 Tor proxy support with IP rotation
- 📂 Outputs results as JSON
- 🛡️ Handles retries, timeouts, and errors gracefully

## Installation
<details>
```bash
git clone https://github.com/PFarahani/async-media-indexer.git
cd async-media-indexer
pip install -r requirements.txt
```
</details>

## Usage
<details>
Run the crawler:

```bash
python main.py
```

Output will be saved to:

```
all_directory_structures.json
```
</details>

## Requirements
<details>
* Python 3.9+
* Dependencies listed in `requirements.txt`
* (Optional) Tor service running locally for proxy rotation
</details>