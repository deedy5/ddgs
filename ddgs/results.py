class SearchResult:
    def __init__(self) -> None:
        self.body = ""
        self.href = ""
        self.title = ""

    def __str__(self) -> str:
        return f"{self.title}\n{self.href}\n{self.body}"

    def __repr__(self) -> str:
        return str(self)
