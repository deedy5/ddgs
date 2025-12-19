![Python >= 3.10](https://img.shields.io/badge/python->=3.10-red.svg) [![](https://badgen.net/github/release/deedy5/ddgs)](https://github.com/deedy5/ddgs/releases) [![](https://badge.fury.io/py/ddgs.svg)](https://pypi.org/project/ddgs)
# DDGS | Dux Distributed Global Search<a name="TOP"></a>

A metasearch library that aggregates results from diverse web search services.


## Table of Contents
* [API Server (with MCP Integration)](#api-server-with-mcp-integration)
* [Install](#install)
* [CLI version](#cli-version)
* [Engines](#engines)
* [DDGS class](#ddgs-class)
* [1. text()](#1-text)
* [2. images()](#2-images)
* [3. videos()](#3-videos)
* [4. news()](#4-news)
* [5. books()](#5-books)
* [Disclaimer](#disclaimer)

___
## API Server (with MCP Integration)
-  **Docker compose**
```bash
git clone https://github.com/deedy5/ddgs && cd ddgs
docker-compose up --build
```
-  **Bash**
```bash
git clone https://github.com/deedy5/ddgs && cd ddgs
chmod +x start_api.sh
./start_api.sh
```

#### Available Endpoints
- MCP Endpoints (for AI assistance):
    - `http://localhost:8000/mcp` - HTTP transport
    - `http://localhost:8000/sse` - SSE transport
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### Available MCP Tools
- `search_text` - Web text searches
- `search_images` - Image searches
- `search_news` - News searches
- `search_videos` - Video searches
- `search_books` - Book searches

[Go To TOP](#TOP)
___

## Install
```python
pip install -U ddgs
```

## CLI version

```python3
ddgs --help
```

[Go To TOP](#TOP)

## Engines

| DDGS function | Available backends |
| --------------|:-------------------|
| text()        | `bing`, `brave`, `duckduckgo`, `google`, `grokipedia`, `mojeek`, `yandex`, `yahoo`, `wikipedia`|
| images()      | `duckduckgo` |
| videos()      | `duckduckgo` |
| news()        | `bing`, `duckduckgo`, `yahoo` |
| books()       | `annasarchive` |

[Go To TOP](#TOP)

## DDGS class

DDGS class is lazy-loaded.

```python3
class DDGS:
    """Dux Distributed Global Search. A metasearch library that aggregates results from diverse web search services.

    Args:
        proxy (str, optional): proxy for the HTTP client, supports http/https/socks5 protocols.
            example: "http://user:pass@example.com:3128". Defaults to None.
        timeout (int, optional): Timeout value for the HTTP client. Defaults to 5.
        verify: (bool | str):  True to verify, False to skip, or a str path to a PEM file. Defaults to True.
    """
```

Here is an example of initializing the DDGS class.
```python3
from ddgs import DDGS

results = DDGS().text("python programming", max_results=5)
print(results)
```

[Go To TOP](#TOP)

## 1. text()

```python
def text(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int | None = 10,
    page: int = 1,
    backend: str = "auto",
) -> list[dict[str, str]]:
    """DDGS text metasearch.

    Args:
        query: text search query.
        region: us-en, uk-en, ru-ru, etc. Defaults to us-en.
        safesearch: on, moderate, off. Defaults to "moderate".
        timelimit: d, w, m, y. Defaults to None.
        max_results: maximum number of results. Defaults to 10.
        page: page of results. Defaults to 1.
        backend: A single or comma-delimited backends. Defaults to "auto".

    Returns:
        List of dictionaries with search results.
    """
```
***Example***
```python
results = DDGS().text('live free or die', region='us-en', safesearch='off', timelimit='y', page=1, backend="auto")
# Searching for pdf files
results = DDGS().text('russia filetype:pdf', region='us-en', safesearch='off', timelimit='y', page=1, backend="auto")
print(results)
[
    {
        "title": "News, sport, celebrities and gossip | The Sun",
        "href": "https://www.thesun.co.uk/",
        "body": "Get the latest news, exclusives, sport, celebrities, showbiz, politics, business and lifestyle from The Sun",
    }, ...
]
```

[Go To TOP](#TOP)

## 2. images()

```python
def images(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int | None = 10,
    page: int = 1,
    backend: str = "auto",
    size: str | None = None,
    color: str | None = None,
    type_image: str | None = None,
    layout: str | None = None,
    license_image: str | None = None,
) -> list[dict[str, str]]:
    """DDGS images metasearch.

    Args:
        query: images search query.
        region: us-en, uk-en, ru-ru, etc. Defaults to us-en.
        safesearch: on, moderate, off. Defaults to "moderate".
        timelimit: d, w, m, y. Defaults to None.
        max_results: maximum number of results. Defaults to 10.
        page: page of results. Defaults to 1.
        backend: A single or comma-delimited backends. Defaults to "auto".
        size: Small, Medium, Large, Wallpaper. Defaults to None.
        color: color, Monochrome, Red, Orange, Yellow, Green, Blue,
            Purple, Pink, Brown, Black, Gray, Teal, White. Defaults to None.
        type_image: photo, clipart, gif, transparent, line.
            Defaults to None.
        layout: Square, Tall, Wide. Defaults to None.
        license_image: any (All Creative Commons), Public (PublicDomain),
            Share (Free to Share and Use), ShareCommercially (Free to Share and Use Commercially),
            Modify (Free to Modify, Share, and Use), ModifyCommercially (Free to Modify, Share, and
            Use Commercially). Defaults to None.

    Returns:
        List of dictionaries with images search results.
    """
```
***Example***
```python
results = DDGS().images(
    query="butterfly",
    region="us-en",
    safesearch="off",
    timelimit="m",
    page=1,
    backend="auto",
    size=None,
    color="Monochrome",
    type_image=None,
    layout=None,
    license_image=None,
)
print(images)
[
    {
        "title": "File:The Sun by the Atmospheric Imaging Assembly of NASA's Solar ...",
        "image": "https://upload.wikimedia.org/wikipedia/commons/b/b4/The_Sun_by_the_Atmospheric_Imaging_Assembly_of_NASA's_Solar_Dynamics_Observatory_-_20100819.jpg",
        "thumbnail": "https://tse4.mm.bing.net/th?id=OIP.lNgpqGl16U0ft3rS8TdFcgEsEe&pid=Api",
        "url": "https://en.wikipedia.org/wiki/File:The_Sun_by_the_Atmospheric_Imaging_Assembly_of_NASA's_Solar_Dynamics_Observatory_-_20100819.jpg",
        "height": 3860,
        "width": 4044,
        "source": "Bing",
    }, ...
]
```

[Go To TOP](#TOP)

## 3. videos()

```python
def videos(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int | None = 10,
    page: int = 1,
    backend: str = "auto",
    resolution: str | None = None,
    duration: str | None = None,
    license_videos: str | None = None,
) -> list[dict[str, str]]:
    """DDGS videos metasearch.

    Args:
        query: videos search query.
        region: us-en, uk-en, ru-ru, etc. Defaults to us-en.
        safesearch: on, moderate, off. Defaults to "moderate".
        timelimit: d, w, m. Defaults to None.
        max_results: maximum number of results. Defaults to 10.
        page: page of results. Defaults to 1.
        backend: A single or comma-delimited backends. Defaults to "auto".
        resolution: high, standart. Defaults to None.
        duration: short, medium, long. Defaults to None.
        license_videos: creativeCommon, youtube. Defaults to None.

    Returns:
        List of dictionaries with videos search results.
    """
```
***Example***
```python
results = DDGS().videos(
    query="cars",
    region="us-en",
    safesearch="off",
    timelimit="w",
    page=1,
    backend="auto",
    resolution="high",
    duration="medium",
)
print(results)
[
    {
        "content": "https://www.youtube.com/watch?v=6901-C73P3g",
        "description": "Watch the Best Scenes of popular Tamil Serial #Meena that airs on Sun TV. Watch all Sun TV serials immediately after the TV telecast on Sun NXT app. *Free for Indian Users only Download here: Android - http://bit.ly/SunNxtAdroid iOS: India - http://bit.ly/sunNXT Watch on the web - https://www.sunnxt.com/ Two close friends, Chidambaram ...",
        "duration": "8:22",
        "embed_html": '<iframe width="1280" height="720" src="https://www.youtube.com/embed/6901-C73P3g?autoplay=1" frameborder="0" allowfullscreen></iframe>',
        "embed_url": "https://www.youtube.com/embed/6901-C73P3g?autoplay=1",
        "image_token": "6c070b5f0e24e5972e360d02ddeb69856202f97718ea6c5d5710e4e472310fa3",
        "images": {
            "large": "https://tse4.mm.bing.net/th?id=OVF.JWBFKm1u%2fHd%2bz2e1GitsQw&pid=Api",
            "medium": "https://tse4.mm.bing.net/th?id=OVF.JWBFKm1u%2fHd%2bz2e1GitsQw&pid=Api",
            "motion": "",
            "small": "https://tse4.mm.bing.net/th?id=OVF.JWBFKm1u%2fHd%2bz2e1GitsQw&pid=Api",
        },
        "provider": "Bing",
        "published": "2024-07-03T05:30:03.0000000",
        "publisher": "YouTube",
        "statistics": {"viewCount": 29059},
        "title": "Meena - Best Scenes | 02 July 2024 | Tamil Serial | Sun TV",
        "uploader": "Sun TV",
    }, ...
]
```

[Go To TOP](#TOP)

## 4. news()

```python
def news(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int | None = 10,
    page: int = 1,
    backend: str = "auto",
) -> list[dict[str, str]]:
    """DDGS news metasearch.

    Args:
        query: news search query.
        region: us-en, uk-en, ru-ru, etc. Defaults to us-en.
        safesearch: on, moderate, off. Defaults to "moderate".
        timelimit: d, w, m. Defaults to None.
        max_results: maximum number of results. Defaults to 10.
        page: page of results. Defaults to 1.
        backend: A single or comma-delimited backends. Defaults to "auto".

    Returns:
        List of dictionaries with news search results.
    """
```
***Example***
```python
results = DDGS().news(query="sun", region="us-en", safesearch="off", timelimit="m", page=1, backend="auto")
print(results)
[
    {
        "date": "2024-07-03T16:25:22+00:00",
        "title": "Murdoch's Sun Endorses Starmer's Labour Day Before UK Vote",
        "body": "Rupert Murdoch's Sun newspaper endorsed Keir Starmer and his opposition Labour Party to win the UK general election, a dramatic move in the British media landscape that illustrates the country's shifting political sands.",
        "url": "https://www.msn.com/en-us/money/other/murdoch-s-sun-endorses-starmer-s-labour-day-before-uk-vote/ar-BB1plQwl",
        "image": "https://img-s-msn-com.akamaized.net/tenant/amp/entityid/BB1plZil.img?w=2000&h=1333&m=4&q=79",
        "source": "Bloomberg on MSN.com",
    }, ...
]
```

[Go To TOP](#TOP)

## 5. books()

```python
def books(
    query: str,
    max_results: int | None = 10,
    page: int = 1,
    backend: str = "auto",
) -> list[dict[str, str]]:
    """DDGS books metasearch.

    Args:
        query: news search query.
        max_results: maximum number of results. Defaults to 10.
        page: page of results. Defaults to 1.
        backend: A single or comma-delimited backends. Defaults to "auto".

    Returns:
        List of dictionaries with news search results.
    """
```
***Example***
```python
results = DDGS().books(query="sea wolf jack london", page=1, backend="auto")
print(results)
[
    {
        'title': 'The Sea-Wolf',
        'author': 'Jack London',
        'publisher': 'DigiCat, 2022',
        'info': 'English [en], .epub, 🚀/zlib, 0.5MB, 📗 Book (unknown)',
        'url': 'https://annas-archive.li/md5/574f6556f1df6717de4044e36c7c2782',
        'thumbnail': 'https://s3proxy.cdn-zlib.sk//covers299/collections/userbooks/da4954486be7c2b2b9f70b2aa5bcf01292de3ea510b5656f892821950ded9ada.jpg',
    }, ...
]
```

[Go To TOP](#TOP)

## Disclaimer

This library is for educational purposes only.
