import httpx

API_URL = "https://api.hardcover.app/v1/graphql"

WANT_TO_READ_QUERY = """
query WantToRead {
  me {
    user_books(where: {status_id: {_eq: 1}}) {
      book {
        id
        title
        slug
        contributions {
          author {
            name
          }
        }
      }
    }
  }
}
"""

IN_DOVER_LIST_SLUG = "in-dover"

IN_DOVER_QUERY = """
query InDoverList($slug: String!) {
  me {
    lists(where: {slug: {_eq: $slug}}) {
      list_books {
        book {
          id
          title
          slug
          contributions {
            author {
              name
            }
          }
        }
      }
    }
  }
}
"""


def _graphql_post(query: str, variables: dict | None = None, token: str = "") -> dict:
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            API_URL,
            json={"query": query, "variables": variables or {}},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise RuntimeError(f"GraphQL error: {result['errors']}")
        return result


def extract_author_name(contributions: list[dict]) -> str:
    if not contributions:
        return "Unknown"
    author = contributions[0].get("author")
    if author is None:
        return "Unknown"
    return author.get("name", "Unknown")


def _parse_book(book: dict) -> dict:
    return {
        "hardcover_id": book["id"],
        "title": book["title"],
        "slug": book.get("slug", ""),
        "author": extract_author_name(book.get("contributions", [])),
    }


def fetch_want_to_read(token: str) -> list[dict]:
    data = _graphql_post(WANT_TO_READ_QUERY, token=token)
    me = data["data"]["me"]
    if not me:
        return []
    user_books = me[0]["user_books"]
    return [_parse_book(ub["book"]) for ub in user_books]


def fetch_in_dover_list(token: str, slug: str = IN_DOVER_LIST_SLUG) -> list[dict]:
    data = _graphql_post(IN_DOVER_QUERY, variables={"slug": slug}, token=token)
    me = data["data"]["me"]
    if not me:
        return []
    lists = me[0]["lists"]
    if not lists:
        return []
    list_books = lists[0]["list_books"]
    return [_parse_book(lb["book"]) for lb in list_books]
