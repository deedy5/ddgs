![Python >= 3.10](https://img.shields.io/badge/python->=3.10-red.svg) [![](https://badgen.net/github/release/deedy5/ddgs)](https://github.com/deedy5/ddgs/releases) [![](https://badge.fury.io/py/ddgs.svg)](https://pypi.org/project/ddgs) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit) [![](https://pepy.tech/badge/ddgs/month)](https://pypistats.org/packages/ddgs)
# DDGS | Dux Distributed Global Search<a name="TOP"></a>

A metasearch library that aggregates results from diverse web search services.


## Table of Contents
* [Install](#install)
* [CLI version](#cli-version)
* [DDGS search operators](#ddgs-search-operators)
* [Regions](#regions)
* [Engines](#engines)
* [Tips](#tips)
* [DDGS class](#ddgs-class)
* [Proxy](#proxy)
* [Exceptions](#exceptions)
* [1. text()](#1-text)
* [2. images()](#2-images)
* [3. videos()](#3-videos)
* [4. news()](#4-news)
* [5. books()](#5-books)
* [Disclaimer](#disclaimer)

## Install
```python
pip install -U ddgs
```

## CLI version

```python3
ddgs --help
```
CLI examples:

a) text:
 - *query='neurophysiology of the flickering light perception'*
 - *region='cn'*
 - *language='zh'*
 - *max_results=5*
 - *backend='google, brave'*
 - *proxy='socks5h://127.0.0.1:9150'* ('tb' is an alias for the Tor browser)

`ddgs text -q 'neurophysiology of the flickering light perception' -r cn-zh -m 5 -b google -b brave -pr tb`

b) news:
 - *query='etna eraption'*
 - *region='it'*
 - *language='it'*
 - *max_results=10*

`ddgs news -q 'etna eruption' -r it-it -m 10`

c) books:
 - *query='dolphins cousteau'*
 - *max_results=100*
 - *output='csv'* (save as csv file)

`ddgs books -q 'dolphins cousteau' -m 100 -o /tmp/books.csv`

[Go To TOP](#TOP)

## DDGS search operators

| Query example |	Result|
| ---     | ---   |
| cats dogs |	Results about cats or dogs |
| "cats and dogs" |	Results for exact term "cats and dogs". If no results are found, related results are shown. |
| cats -dogs |	Fewer dogs in results |
| cats +dogs |	More dogs in results |
| cats filetype:pdf |	PDFs about cats. Supported file types: pdf, doc(x), xls(x), ppt(x), html |
| dogs site:example.com  |	Pages about dogs from example.com |
| cats -site:example.com |	Pages about cats, excluding example.com |
| intitle:dogs |	Page title includes the word "dogs" |
| inurl:cats  |	Page url includes the word "cats" |

[Go To TOP](#TOP)

## Regions
<details>
  <summary>expand</summary>

    xa-ar for Arabia
    xa-en for Arabia (en)
    ar-es for Argentina
    au-en for Australia
    at-de for Austria
    be-fr for Belgium (fr)
    be-nl for Belgium (nl)
    br-pt for Brazil
    bg-bg for Bulgaria
    ca-en for Canada
    ca-fr for Canada (fr)
    ct-ca for Catalan
    cl-es for Chile
    cn-zh for China
    co-es for Colombia
    hr-hr for Croatia
    cz-cs for Czech Republic
    dk-da for Denmark
    ee-et for Estonia
    fi-fi for Finland
    fr-fr for France
    de-de for Germany
    gr-el for Greece
    hk-tzh for Hong Kong
    hu-hu for Hungary
    in-en for India
    id-id for Indonesia
    id-en for Indonesia (en)
    ie-en for Ireland
    il-he for Israel
    it-it for Italy
    jp-jp for Japan
    kr-kr for Korea
    lv-lv for Latvia
    lt-lt for Lithuania
    xl-es for Latin America
    my-ms for Malaysia
    my-en for Malaysia (en)
    mx-es for Mexico
    nl-nl for Netherlands
    nz-en for New Zealand
    no-no for Norway
    pe-es for Peru
    ph-en for Philippines
    ph-tl for Philippines (tl)
    pl-pl for Poland
    pt-pt for Portugal
    ro-ro for Romania
    ru-ru for Russia
    sg-en for Singapore
    sk-sk for Slovak Republic
    sl-sl for Slovenia
    za-en for South Africa
    es-es for Spain
    se-sv for Sweden
    ch-de for Switzerland (de)
    ch-fr for Switzerland (fr)
    ch-it for Switzerland (it)
    tw-tzh for Taiwan
    th-th for Thailand
    tr-tr for Turkey
    ua-uk for Ukraine
    uk-en for United Kingdom
    us-en for United States
    ue-es for United States (es)
    ve-es for Venezuela
    vn-vi for Vietnam
___
</details>

[Go To TOP](#TOP)

## Engines

| DDGS function | Available backends |
| --------------|:-------------------|
| text()        | `bing`, `brave`, `duckduckgo`, `google`, `mojeek`, `yandex`, `yahoo`, `wikipedia`|
| images()      | `duckduckgo` |
| videos()      | `duckduckgo` |
| news()        | `bing`, `duckduckgo`, `yahoo` |
| books()       | `annasarchive` |

[Go To TOP](#TOP)

## Tips

⚠️ **For optimal usage, keep `backend='auto'`** (the default) and specify the desired number of results with `max_results`. This allows the library to automatically handle temporary backend unavailability.

The library considers:

    - Duplicate providers (e.g., yahoo = bing)
    - Result repeatability, prioritizing frequently repeated positions
    - Wikipedia summaries at the top of results, if available

To customize the search engine order, provide the backends as a comma-separated string (for example: `backend="google, brave, yahoo"`). The library will query them in order, falling back to the next one if an error occurs.

The library works in parallel, adjusting concurrent requests based on `max_results`. This ensures efficient and fast retrieval. You can change the maximum number of threads using the parameter `DDGS.threads` (for example, `DDGS.threads = 20`).

Note that a single query returns results from one page (`page=1`) of the selected backends; iterate over pages for more results. Setting `max_results` to None returns all unique collected results.

The `region` parameter also has a strong influence on the quality of the search. Set it as `{country}-{language}`: `ar-es`, `pl-pl`, `cn-zh`, etc.

Note that some backends may be temporarily unavailable due to ratelimiting or ISP blockages in certain countries. In such cases, using a proxy server can help bypass these restrictions.

[Go To TOP](#TOP)

## DDGS class

DDGS class is lazy-loaded.

When you import DDGS nothing is executed — no implementation or dependencies are loaded. The actual DDGS class and its heavy imports are loaded lazily the first time you instantiate or otherwise access DDGS, keeping import-time overhead minimal for downstream code.

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

## Proxy

Package supports http/https/socks proxies. Example: `http://user:pass@example.com:3128`.
Use a rotating proxy. Otherwise, use a new proxy with each DDGS class initialization.

*1. The easiest way. Launch the Tor Browser*
```python3
ddgs = DDGS(proxy="tb", timeout=10)  # "tb" is an alias for "socks5h://127.0.0.1:9150"
results = ddgs.text("something you need", max_results=50)
```
*2. Use any proxy server*
```python3
ddgs = DDGS(proxy="socks5h://user:password@1.2.3.4:8080", timeout=10)
results = ddgs.text("something you need", max_results=50)
```
*3. The proxy can also be set using the `DDGS_PROXY` environment variable.*
```python3
export DDGS_PROXY="socks5h://user:password@1.2.3.4:8080"
```

[Go To TOP](#TOP)

## Exceptions

```python
from ddgs.exceptions import (
    DDGSException,
    RatelimitException,
    TimeoutException,
)
```

Exceptions:
- `DDGSException`: Base exception for ddgs errors.
- `RatelimitException`: Inherits from DDGSException, raised for exceeding API request rate limits.
- `TimeoutException`: Inherits from DDGSException, raised for API request timeouts.

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
    hide_ai_images: bool | None = None,
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
        hide_ai_images: exclude AI generated images from results.

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
