"""CLI tool for DDGS."""

import csv
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import click
import primp

from . import __version__
from .ddgs import DDGS
from .utils import _expand_proxy_tb_alias

logger = logging.getLogger(__name__)

COLORS = {
    0: "black",
    1: "red",
    2: "green",
    3: "yellow",
    4: "blue",
    5: "magenta",
    6: "cyan",
    7: "bright_black",
    8: "bright_red",
    9: "bright_green",
    10: "bright_yellow",
    11: "bright_blue",
    12: "bright_magenta",
    13: "bright_cyan",
    14: "white",
    15: "bright_white",
}


def _convert_tuple_to_csv(_ctx: click.Context, _param: click.Parameter, value: tuple[str] | None) -> str:
    if value is not None and isinstance(value, tuple):
        return ",".join(value)
    return ""


def _save_data(query: str, data: list[dict[str, str]], function_name: str, filename: str | None) -> None:
    filename, ext = filename.rsplit(".", 1) if filename and filename.endswith((".csv", ".json")) else (None, filename)
    filename = filename if filename else f"{function_name}_{query}_{datetime.now(tz=timezone.utc):%Y%m%d_%H%M%S}"
    if ext == "csv":
        _save_csv(f"{filename}.{ext}", data)
    elif ext == "json":
        _save_json(f"{filename}.{ext}", data)


def _save_json(jsonfile: str | Path, data: list[dict[str, str]]) -> None:
    with Path(jsonfile).open("w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False, indent=2))


def _save_csv(csvfile: str | Path, data: list[dict[str, str]]) -> None:
    with Path(csvfile).open("w", newline="", encoding="utf-8") as file:
        if data:
            headers = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(data)


def _print_data(data: list[dict[str, str]]) -> None:
    if data:
        for i, e in enumerate(data, start=1):
            click.secho(f"{i}.\t    {'=' * 78}", bg="black", fg="white")
            for j, (k, v) in enumerate(e.items(), start=1):
                if v:
                    width = 300 if k in ("content", "href", "image", "source", "thumbnail", "url") else 78
                    title = "language" if k == "detected_language" else k
                    text = click.wrap_text(
                        f"{v}",
                        width=width,
                        initial_indent="",
                        subsequent_indent=" " * 12,
                        preserve_paragraphs=True,
                    )
                else:
                    title = k
                    text = v
                click.secho(f"{title:<12}{text}", bg="black", fg=COLORS[j], overline=True)
            input()


def _sanitize_query(query: str) -> str:
    return (
        query.replace("filetype", "")
        .replace(":", "")
        .replace('"', "'")
        .replace("site", "")
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "")
    )


def _download_file(url: str, dir_path: str, filename: str, proxy: str | None, *, verify: bool) -> None:
    try:
        resp = primp.Client(proxy=proxy, impersonate="random", impersonate_os="random", timeout=10, verify=verify).get(
            url,
        )
        if resp.status_code == 200:
            f = Path(dir_path) / filename[:200]
            with f.open("wb") as file:
                file.write(resp.content)
    except Exception as ex:  # noqa: BLE001
        logger.debug("Error download_file url=%s: %r", url, ex)


def _download_results(
    query: str,
    results: list[dict[str, str]],
    function_name: str,
    proxy: str | None = None,
    threads: int | None = None,
    pathname: str | None = None,
    *,
    verify: bool = True,
) -> None:
    path = pathname if pathname else f"{function_name}_{query}_{datetime.now(tz=timezone.utc):%Y%m%d_%H%M%S}"
    Path(path).mkdir(parents=True, exist_ok=True)

    threads = 10 if threads is None else threads
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for i, res in enumerate(results, start=1):
            url = res["image"] if function_name == "images" else res["href"]
            filename = unquote(url.split("/")[-1].split("?")[0])
            f = executor.submit(_download_file, url, path, f"{i}_{filename}", proxy, verify=verify)
            futures.append(f)

        with click.progressbar(
            length=len(futures),
            label="Downloading",
            show_percent=True,
            show_pos=True,
            width=50,
        ) as bar:
            for future in as_completed(futures):
                future.result()
                bar.update(1)


@click.group(chain=True)
def cli() -> None:
    """DDGS CLI tool."""


def safe_entry_point() -> None:
    """Run the CLI tool in try-except block to catch all exceptions."""
    logging.basicConfig(level=logging.WARNING)
    try:
        cli()
    except Exception as ex:  # noqa: BLE001
        click.echo(f"{type(ex).__name__}: {ex!r}")


@cli.command()
def version() -> str:
    """Print and return version."""
    print(__version__)  # noqa: T201
    return __version__


@cli.command()
@click.option("-q", "--query", help="text search query")
@click.option("-k", "--keywords", help="(Deprecated) text search query")  # deprecated
@click.option("-r", "--region", default="us-en", help="us-en, ru-ru, etc.")
@click.option("-s", "--safesearch", default="moderate", type=click.Choice(["on", "moderate", "off"]))
@click.option("-t", "--timelimit", type=click.Choice(["d", "w", "m", "y"]), help="day, week, month, year")
@click.option("-m", "--max_results", default=10, type=int, help="maximum number of results")
@click.option("-p", "--page", default=1, type=int, help="page number of results")
@click.option(
    "-b",
    "--backend",
    default=["auto"],
    type=click.Choice(
        [
            "auto",
            "all",
            "bing",
            "brave",
            "duckduckgo",
            "google",
            "mojeek",
            "yandex",
            "yahoo",
            "wikipedia",
        ],
    ),
    multiple=True,
    callback=_convert_tuple_to_csv,
)
@click.option("-o", "--output", help="csv, json or filename.csv|json (save the results to a csv or json file)")
@click.option("-d", "--download", is_flag=True, default=False, help="download results. -dd to set custom directory")
@click.option("-dd", "--download-directory", help="Specify custom download directory")
@click.option("-th", "--threads", default=10, help="download threads, default=10")
@click.option("-pr", "--proxy", help="the proxy to send requests, example: socks5h://127.0.0.1:9150")
@click.option("-v", "--verify", default=True, help="verify SSL when making the request")
def text(
    query: str,
    keywords: str | None,  # deprecated
    region: str,
    safesearch: str,
    timelimit: str | None,
    max_results: int | None,
    page: int,
    backend: str,
    output: str | None,
    download_directory: str | None,
    threads: int,
    proxy: str | None,
    *,
    download: bool,
    verify: bool,
) -> None:
    """CLI function to perform a DDGS text metasearch."""
    data = DDGS(proxy=_expand_proxy_tb_alias(proxy), verify=verify).text(
        query=query,
        keywords=keywords,  # deprecated
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results,
        page=page,
        backend=backend,
    )
    query = _sanitize_query(query)
    if output:
        _save_data(query, data, "text", filename=output)
    if download:
        _download_results(
            query,
            data,
            function_name="text",
            proxy=proxy,
            threads=threads,
            verify=verify,
            pathname=download_directory,
        )
    if not output and not download:
        _print_data(data)


@cli.command()
@click.option("-q", "--query", help="images search query")
@click.option("-k", "--keywords", help="(Deprecated) images search query")  # deprecated
@click.option("-r", "--region", default="us-en", help="us-en, ru-ru, etc.")
@click.option("-s", "--safesearch", default="moderate", type=click.Choice(["on", "moderate", "off"]))
@click.option("-t", "--timelimit", type=click.Choice(["d", "w", "m", "y"]))
@click.option("-m", "--max_results", default=10, type=int, help="maximum number of results")
@click.option("-p", "--page", default=1, type=int, help="page number of results")
@click.option(
    "-b",
    "--backend",
    default=["auto"],
    type=click.Choice(["auto", "all", "duckduckgo"]),
    multiple=True,
    callback=_convert_tuple_to_csv,
)
@click.option("-size", "--size", type=click.Choice(["Small", "Medium", "Large", "Wallpaper"]))
@click.option(
    "-c",
    "--color",
    type=click.Choice(
        [
            "color",
            "Monochrome",
            "Red",
            "Orange",
            "Yellow",
            "Green",
            "Blue",
            "Purple",
            "Pink",
            "Brown",
            "Black",
            "Gray",
            "Teal",
            "White",
        ],
    ),
)
@click.option("-type", "--type_image", type=click.Choice(["photo", "clipart", "gif", "transparent", "line"]))
@click.option("-l", "--layout", type=click.Choice(["Square", "Tall", "Wide"]))
@click.option(
    "-lic",
    "--license_image",
    type=click.Choice(["any", "Public", "Share", "ShareCommercially", "Modify", "ModifyCommercially"]),
)
@click.option("-o", "--output", help="csv, json or filename.csv|json (save the results to a csv or json file)")
@click.option("-d", "--download", is_flag=True, default=False, help="download results. -dd to set custom directory")
@click.option("-dd", "--download-directory", help="Specify custom download directory")
@click.option("-th", "--threads", default=10, help="download threads, default=10")
@click.option("-pr", "--proxy", help="the proxy to send requests, example: socks5h://127.0.0.1:9150")
@click.option("-v", "--verify", default=True, help="verify SSL when making the request")
def images(
    query: str,
    keywords: str | None,  # deprecated
    region: str,
    safesearch: str,
    timelimit: str | None,
    max_results: int | None,
    page: int,
    backend: str,
    size: str | None,
    color: str | None,
    type_image: str | None,
    layout: str | None,
    license_image: str | None,
    download_directory: str | None,
    threads: int,
    output: str | None,
    proxy: str | None,
    *,
    download: bool,
    verify: bool,
) -> None:
    """CLI function to perform a DDGS images metasearch."""
    data = DDGS(proxy=_expand_proxy_tb_alias(proxy), verify=verify).images(
        query=query,
        keywords=keywords,  # deprecated
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results,
        page=page,
        backend=backend,
        size=size,
        color=color,
        type_image=type_image,
        layout=layout,
        license_image=license_image,
    )
    query = _sanitize_query(query)
    if output:
        _save_data(query, data, function_name="images", filename=output)
    if download:
        _download_results(
            query,
            data,
            function_name="images",
            proxy=proxy,
            threads=threads,
            verify=verify,
            pathname=download_directory,
        )
    if not output and not download:
        _print_data(data)


@cli.command()
@click.option("-q", "--query", help="videos search query")
@click.option("-k", "--keywords", help="(Deprecated) videos search query")  # deprecated
@click.option("-r", "--region", default="us-en", help="us-en, ru-ru, etc.")
@click.option("-s", "--safesearch", default="moderate", type=click.Choice(["on", "moderate", "off"]))
@click.option("-t", "--timelimit", type=click.Choice(["d", "w", "m"]), help="day, week, month")
@click.option("-m", "--max_results", default=10, type=int, help="maximum number of results")
@click.option("-p", "--page", default=1, type=int, help="page number of results")
@click.option(
    "-b",
    "--backend",
    default=["auto"],
    type=click.Choice(["auto", "all", "duckduckgo"]),
    multiple=True,
    callback=_convert_tuple_to_csv,
)
@click.option("-res", "--resolution", type=click.Choice(["high", "standart"]))
@click.option("-d", "--duration", type=click.Choice(["short", "medium", "long"]))
@click.option("-lic", "--license_videos", type=click.Choice(["creativeCommon", "youtube"]))
@click.option("-o", "--output", help="csv, json or filename.csv|json (save the results to a csv or json file)")
@click.option("-pr", "--proxy", help="the proxy to send requests, example: socks5h://127.0.0.1:9150")
@click.option("-v", "--verify", default=True, help="verify SSL when making the request")
def videos(
    query: str,
    keywords: str | None,  # deprecated
    region: str,
    safesearch: str,
    timelimit: str | None,
    max_results: int | None,
    page: int,
    backend: str,
    resolution: str | None,
    duration: str | None,
    license_videos: str | None,
    output: str | None,
    proxy: str | None,
    *,
    verify: bool,
) -> None:
    """CLI function to perform a DDGS videos metasearch."""
    data = DDGS(proxy=_expand_proxy_tb_alias(proxy), verify=verify).videos(
        query=query,
        keywords=keywords,  # deprecated
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results,
        page=page,
        backend=backend,
        resolution=resolution,
        duration=duration,
        license_videos=license_videos,
    )
    query = _sanitize_query(query)
    if output:
        _save_data(query, data, function_name="videos", filename=output)
    else:
        _print_data(data)


@cli.command()
@click.option("-q", "--query", help="news search query")
@click.option("-k", "--keywords", help="(Deprecated) news search query")  # deprecated
@click.option("-r", "--region", default="us-en", help="us-en, ru-ru, etc.")
@click.option("-s", "--safesearch", default="moderate", type=click.Choice(["on", "moderate", "off"]))
@click.option("-t", "--timelimit", type=click.Choice(["d", "w", "m", "y"]), help="day, week, month, year")
@click.option("-m", "--max_results", default=10, type=int, help="maximum number of results")
@click.option("-p", "--page", default=1, type=int, help="page number of results")
@click.option(
    "-b",
    "--backend",
    default=["auto"],
    type=click.Choice(["auto", "all", "bing", "duckduckgo", "yahoo"]),
    multiple=True,
    callback=_convert_tuple_to_csv,
)
@click.option("-o", "--output", help="csv, json or filename.csv|json (save the results to a csv or json file)")
@click.option("-pr", "--proxy", help="the proxy to send requests, example: socks5h://127.0.0.1:9150")
@click.option("-v", "--verify", default=True, help="verify SSL when making the request")
def news(
    query: str,
    keywords: str | None,  # deprecated
    region: str,
    safesearch: str,
    timelimit: str | None,
    max_results: int | None,
    page: int,
    backend: str,
    output: str | None,
    proxy: str | None,
    *,
    verify: bool,
) -> None:
    """CLI function to perform a DDGS news metasearch."""
    data = DDGS(proxy=_expand_proxy_tb_alias(proxy), verify=verify).news(
        query=query,
        keywords=keywords,  # deprecated
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results,
        page=page,
        backend=backend,
    )
    query = _sanitize_query(query)
    if output:
        _save_data(query, data, function_name="news", filename=output)
    else:
        _print_data(data)


@cli.command()
@click.option("-q", "--query", help="books search query")
@click.option("-k", "--keywords", help="(Deprecated) books search query")  # deprecated
@click.option("-m", "--max_results", default=10, type=int, help="maximum number of results")
@click.option("-p", "--page", default=1, type=int, help="page number of results")
@click.option(
    "-b",
    "--backend",
    default=["auto"],
    type=click.Choice(["auto", "all", "annasarchive"]),
    multiple=True,
    callback=_convert_tuple_to_csv,
)
@click.option("-o", "--output", help="csv, json or filename.csv|json (save the results to a csv or json file)")
@click.option("-pr", "--proxy", help="the proxy to send requests, example: socks5h://127.0.0.1:9150")
@click.option("-v", "--verify", default=True, help="verify SSL when making the request")
def books(
    query: str,
    keywords: str | None,  # deprecated
    max_results: int | None,
    page: int,
    backend: str,
    output: str | None,
    proxy: str | None,
    *,
    verify: bool,
) -> None:
    """CLI function to perform a DDGS books metasearch."""
    data = DDGS(proxy=_expand_proxy_tb_alias(proxy), verify=verify).books(
        query=query,
        keywords=keywords,  # deprecated
        max_results=max_results,
        page=page,
        backend=backend,
    )
    if output:
        _save_data(query, data, function_name="books", filename=output)
    else:
        _print_data(data)


if __name__ == "__main__":
    safe_entry_point()
