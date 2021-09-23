from pathlib import Path

import click
import httpx
import pytest
import respx

from src.iDAQcli import get_logs_page

LOGS_URL = httpx.URL(r"http://192.168.1.2/logs.cgi")
DL_PATH = Path()

SAMPLE_PAGE = Path("./tests/has_logs.html")
SAMPLE_HTML = SAMPLE_PAGE.read_text()


def test_unreachable(respx_mock: respx.Router) -> None:
    respx_mock.get(LOGS_URL).mock(side_effect=httpx.ConnectError)
    with pytest.raises(click.Abort):
        get_logs_page(LOGS_URL)


def test_timeout(respx_mock: respx.Router) -> None:
    respx_mock.get(LOGS_URL).mock(side_effect=httpx.ConnectTimeout)
    with pytest.raises(click.Abort):
        get_logs_page(LOGS_URL)


def test_good_comms(respx_mock: respx.Router) -> None:
    respx_mock.get(LOGS_URL).respond(html=SAMPLE_HTML)
    src = get_logs_page(LOGS_URL)
    assert src == SAMPLE_HTML


def test_unhandled_error(respx_mock: respx.Router) -> None:
    respx_mock.get(LOGS_URL).mock(side_effect=httpx.RequestError)
    with pytest.raises(click.Abort):
        get_logs_page(LOGS_URL)
