import asynctest


def get_cursor(test_feeds):
    """
    Returns Cursor Mock for aiopg

    :param test_feeds: Dummy data to return when called fetchall
    :return: Cursor mock
    """
    return asynctest.CoroutineMock(
        execute=asynctest.CoroutineMock(),
        fetchall=asynctest.CoroutineMock(return_value=test_feeds))


class ClientResponse:
    content = None
    status = None

    def __init__(self, content, status):
        self.content = content
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

    async def text(self):
        return self.content


def get_session(content, status):
    """
    Returns mock for aiohttp client

    :param content: response.content
    :param status: response.status
    :return: session and response mock
    """
    resp = ClientResponse(content, status)
    response = asynctest.MagicMock(return_value=resp)
    session = asynctest.MagicMock()
    session.return_value.get.side_effect = response
    return session, response
