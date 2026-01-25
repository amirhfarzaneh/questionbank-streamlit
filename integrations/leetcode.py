from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class LeetCodeProblemMetadata:
    problem_id: int | None
    title: str


_LEETCODE_HOST_SUFFIX = "leetcode.com"


def is_leetcode_problem_url(raw: str) -> bool:
    raw = (raw or "").strip()
    if not raw:
        return False

    try:
        parsed = urlparse(raw)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc.lower().endswith(_LEETCODE_HOST_SUFFIX):
        return False

    return "/problems/" in (parsed.path or "")


def _extract_problem_slug(url: str) -> str | None:
    """Extracts the LeetCode problem slug from a URL.

    Examples:
    - https://leetcode.com/problems/two-sum/
    - https://leetcode.com/problems/two-sum/description/
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return None

    path = (parsed.path or "").strip("/")
    parts = path.split("/")
    try:
        idx = parts.index("problems")
    except ValueError:
        return None

    if idx + 1 >= len(parts):
        return None

    slug = parts[idx + 1].strip()
    return slug or None


def _extract_title_from_html(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        return str(og.get("content")).strip()

    if soup.title and soup.title.string:
        return str(soup.title.string).strip()

    return None


_TITLE_RE = re.compile(r"^\s*(?P<num>\d+)\.\s*(?P<name>.*?)\s*-\s*LeetCode\s*$", re.IGNORECASE)


def _parse_title(title: str) -> LeetCodeProblemMetadata:
    title = (title or "").strip()
    m = _TITLE_RE.match(title)
    if m:
        return LeetCodeProblemMetadata(problem_id=int(m.group("num")), title=m.group("name").strip())

    # Fallback: strip trailing "- LeetCode" if present
    cleaned = re.sub(r"\s*-\s*LeetCode\s*$", "", title, flags=re.IGNORECASE).strip()
    return LeetCodeProblemMetadata(problem_id=None, title=cleaned or title)


def _fetch_via_graphql(url: str, *, timeout_s: float = 15.0) -> LeetCodeProblemMetadata:
    slug = _extract_problem_slug(url)
    if not slug:
        return LeetCodeProblemMetadata(problem_id=None, title=url)

    gql_url = "https://leetcode.com/graphql"
    query = """
    query getQuestionDetail($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionFrontendId
        title
      }
    }
    """.strip()

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; questionbank-streamlit/1.0)",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/problems/{slug}/",
        "Origin": "https://leetcode.com",
    }

    payload = {"query": query, "variables": {"titleSlug": slug}}
    resp = requests.post(gql_url, json=payload, headers=headers, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json() or {}

    question = (data.get("data") or {}).get("question")
    if not question:
        # Sometimes LeetCode returns errors for bad slugs
        return LeetCodeProblemMetadata(problem_id=None, title=slug)

    title = (question.get("title") or "").strip() or slug
    frontend_id = (question.get("questionFrontendId") or "").strip()
    problem_id = None
    try:
        if frontend_id:
            problem_id = int(frontend_id)
    except Exception:
        problem_id = None

    return LeetCodeProblemMetadata(problem_id=problem_id, title=title)


def fetch_leetcode_problem_metadata(url: str, *, timeout_s: float = 15.0) -> LeetCodeProblemMetadata:
    """Fetches minimal metadata (problem number + title) from a LeetCode problem URL.

    Uses the page title / og:title. Does not scrape the problem statement.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; questionbank-streamlit/1.0)",
        "Accept-Language": "en-US,en;q=0.9",
    }

    resp = requests.get(url, headers=headers, timeout=timeout_s)
    if resp.status_code == 403:
        # LeetCode often blocks HTML fetches; GraphQL usually works without auth.
        return _fetch_via_graphql(url, timeout_s=timeout_s)
    resp.raise_for_status()

    title = _extract_title_from_html(resp.text)
    if title:
        return _parse_title(title)

    # Fallback if HTML structure changes.
    return _fetch_via_graphql(url, timeout_s=timeout_s)
