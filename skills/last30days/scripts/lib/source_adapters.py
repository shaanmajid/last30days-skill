"""Minimal source adapter registry for simple pipeline sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import github, hackernews, polymarket, schema


@dataclass(frozen=True)
class SourceRequest:
    subquery: schema.SubQuery
    date_range: tuple[str, str]
    config: dict
    depth: str


FetchResult = tuple[list[dict], dict]
FetchFn = Callable[[SourceRequest], FetchResult]


@dataclass(frozen=True)
class SourceAdapter:
    name: str
    fetch: FetchFn
    always_available: bool = False


class SourceRegistry:
    def __init__(self, adapters: list[SourceAdapter]) -> None:
        self._adapters = {adapter.name: adapter for adapter in adapters}

    def get(self, source: str) -> SourceAdapter | None:
        return self._adapters.get(source)

    def always_available_names(self) -> list[str]:
        return [
            adapter.name
            for adapter in self._adapters.values()
            if adapter.always_available
        ]


def _fetch_hackernews(request: SourceRequest) -> FetchResult:
    from_date, to_date = request.date_range
    result = hackernews.search_hackernews(
        request.subquery.search_query,
        from_date,
        to_date,
        depth=request.depth,
    )
    return hackernews.parse_hackernews_response(result, query=request.subquery.search_query), {}


def _fetch_polymarket(request: SourceRequest) -> FetchResult:
    from_date, to_date = request.date_range
    result = polymarket.search_polymarket(
        request.subquery.search_query,
        from_date,
        to_date,
        depth=request.depth,
    )
    return polymarket.parse_polymarket_response(result, topic=request.subquery.search_query), {}


def _fetch_github(request: SourceRequest) -> FetchResult:
    from_date, to_date = request.date_range
    token = github.resolve_token(request.config.get("GITHUB_TOKEN"))
    response = github.search_github(
        request.subquery.search_query,
        from_date,
        to_date,
        depth=request.depth,
        token=token,
    )
    items = github.parse_github_response(response)
    # An unauth rate-limit response is expected on the tokenless anonymous tier;
    # github.search_github logs it and parse_github_response returns empty.
    items = github.enrich_with_comments(items, depth=request.depth, token=token)
    return items, {}


SOURCE_REGISTRY = SourceRegistry([
    SourceAdapter("hackernews", _fetch_hackernews, always_available=True),
    SourceAdapter("polymarket", _fetch_polymarket, always_available=True),
    SourceAdapter("github", _fetch_github, always_available=True),
])
