import typing as t
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from src.iDAQcli import iDAQlog, parse_iDAQ_log_page

BASE_URL = httpx.URL(r"http://192.168.1.2/")
TEST_PAGE = Path("./tests/testpage.html")

TRUTH_LOGS = [
    [
        {
            "base_url": BASE_URL,
            "log_name": "LOG.001",
            "log_url": "/WAMORE/LOG.001",
            "nbytes": 447_421,
            "log_datetime": datetime.strptime(
                "2017-08-24 21:30:22", iDAQlog._dateformat_in
            ).replace(tzinfo=timezone.utc),
        },
        httpx.URL(r"http://192.168.1.2/WAMORE/LOG.001"),
        "LOG.001    0.43 MB   2017-08-24 21:30:22",
    ],
    [
        {
            "base_url": BASE_URL,
            "log_name": "LOG.002",
            "log_url": "/WAMORE/LOG.002",
            "nbytes": 90_293,
            "log_datetime": datetime.strptime(
                "2017-08-24 21:31:14", iDAQlog._dateformat_in
            ).replace(tzinfo=timezone.utc),
        },
        httpx.URL(r"http://192.168.1.2/WAMORE/LOG.002"),
        "LOG.002    0.09 MB   2017-08-24 21:31:14",
    ],
]


@pytest.fixture
def parsed_log_page() -> t.List[iDAQlog]:
    src = TEST_PAGE.read_text()
    return parse_iDAQ_log_page(src, BASE_URL)


def test_log_page_parsing(parsed_log_page: t.List[iDAQlog]) -> None:
    assert len(parsed_log_page) == len(TRUTH_LOGS)

    for log, truth_spec in zip(parsed_log_page, TRUTH_LOGS):
        truth_attrs, dl_url, formatted_str = truth_spec

        for truth_attr, val in truth_attrs.items():  # type: ignore[attr-defined]
            assert getattr(log, truth_attr) == val

        assert log.dl_url == dl_url

        assert str(log) == formatted_str
