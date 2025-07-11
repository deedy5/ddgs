class TextResult:
    def __init__(self) -> None:
        self.title = ""
        self.href = ""
        self.body = ""

    def __str__(self) -> str:
        return f"{self.title}\n{self.href}\n{self.body}"

    def __repr__(self) -> str:
        return str(self)


class ImagesResult:
    def __init__(self) -> None:
        self.title = ""
        self.image = ""
        self.thumbnail = ""
        self.url = ""
        self.height = ""
        self.width = ""
        self.source = ""

    def __str__(self) -> str:
        return f"{self.title}\n{self.image}\n{self.thumbnail}\n{self.url}\n{self.height}\n{self.width}\n{self.source}"

    def __repr__(self) -> str:
        return str(self)


class NewsResult:
    def __init__(self) -> None:
        self.date: str
        self.title: str
        self.body: str
        self.url: str
        self.image: str
        self.source: str

    def __str__(self) -> str:
        return f"{self.date}\n{self.title}\n{self.body}\n{self.url}\n{self.image}\n{self.source}"

    def __repr__(self) -> str:
        return str(self)


class VideosResult:
    def __init__(self) -> None:
        self.title: str
        self.content: str
        self.description: str
        self.duration: str
        self.embed_html: str
        self.embed_url: str
        self.image_token: str
        self.images: dict[str, str]
        self.provider: str
        self.published: str
        self.publisher: str
        self.statistics: dict[str, str]
        self.uploader: str

    def __str__(self) -> str:
        return f"{self.title}\n{self.embed_html}\n{self.description}\n{self.published}\n{self.publisher}\n{self.statistics}\n{self.content}"  # noqa

    def __repr__(self) -> str:
        return str(self)
