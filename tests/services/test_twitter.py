"""Twitter tests."""
from atuyka.services import twitter


async def test_twitter_headers():
    client = twitter.Twitter()

    headers = await client.get_headers()

    assert headers["Content-Type"] == "application/json"
    assert len(headers["User-Agent"]) > 20
    assert headers["x-guest-token"].isnumeric()
