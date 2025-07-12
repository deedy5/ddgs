import re


class JaccardRanker:
    """
    Rank documents by Jaccard similarity to a query.
    """

    def __init__(
        self,
        min_token_length: int = 3,
        key_fields: tuple[str, ...] = ("title", "body", "description"),
    ) -> None:
        """
        Args:
            min_token_length: minimum length of tokens to keep
            key_fields: which fields of each result to combine for scoring
        """
        self.min_token_length = min_token_length
        self.key_fields = tuple(key_fields)

    def tokenize(self, text: str) -> set[str]:
        """
        Very simple tokenizer:
        - lowercases
        - splits on non-alphanumeric
        - filters out short tokens
        """
        raw_tokens = re.split(r"\W+", text.lower())
        return {tok for tok in raw_tokens if len(tok) >= self.min_token_length}

    def jaccard_score(self, q_tokens: set[str], d_tokens: set[str]) -> float:
        """
        Compute Jaccard similarity: |intersection| / |union|.
        Returns 0.0 if either set is empty.
        """
        if not q_tokens or not d_tokens:
            return 0.0

        intersection = q_tokens & d_tokens
        union = q_tokens | d_tokens
        return len(intersection) / len(union)

    def rank(self, results: list[dict[str, str]], query: str) -> list[dict[str, str]]:
        """
        Rank a list of result-dicts by their Jaccard similarity to `query`.

        Args:
            results: list of dicts, each having whatever fields you want (e.g. 'title','body','href')
            query: the user-supplied query string

        Returns:
            a new list of dicts sorted from most similar to least similar
        """
        # Tokenize the query once
        q_tokens = self.tokenize(query)

        scored: list[tuple[float, dict[str, str]]] = []
        for doc in results:
            # combine all fields into one string
            combined = " ".join(doc.get(field, "") for field in self.key_fields)
            d_tokens = self.tokenize(combined)

            score = self.jaccard_score(q_tokens, d_tokens)
            scored.append((score, doc))

        # Sort descending by score
        scored.sort(key=lambda pair: pair[0], reverse=True)

        # Return only the documents, ordered
        return [doc for (_, doc) in scored]
