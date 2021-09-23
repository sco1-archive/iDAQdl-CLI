import re
import typing as t
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve

import click
import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm

_TIMEOUT = 5  # Global timeout, seconds


class iDAQlog:  # noqa: N801

    _dateformat_in = r"%Y-%m-%d %H:%M:%S"
    _dateformat_out = r"%Y-%m-%d %H:%M:%S"

    def __init__(
        self, base_url: httpx.URL, log_name: str, log_url: str, n_bytes: str, log_date: str
    ) -> None:
        self.extension = ".iDAQ"
        self.base_url = base_url
        self.log_name = log_name
        self.log_url = log_url
        self.nbytes = int(n_bytes)
        self.log_datetime = datetime.strptime(log_date, self._dateformat_in).replace(
            tzinfo=timezone.utc
        )

    def __str__(self) -> str:
        mebibytes = self.nbytes / 1_048_576
        return (
            f"{self.log_name:8s}{mebibytes: 7.2f} MB"
            f"{self.log_datetime.strftime(self._dateformat_out):>22s}"
        )

    @property
    def dl_url(self) -> httpx.URL:
        return self.base_url.copy_with(path=self.log_url)


def get_logs_page(logs_url: httpx.URL) -> str:
    click.secho(f"Contacting {logs_url} ...", fg="green")
    try:
        r = httpx.get(logs_url, timeout=_TIMEOUT)
        html = r.text
    except httpx.HTTPError as err:
        if isinstance(err, httpx.NetworkError):
            click.secho(
                (
                    "Cannot connect to iDAQ\n\n"
                    "Verify iDAQ is connected and powered on\n"
                    "Verify ethernet adapter is configured with a static IP of 192.168.1.1"
                ),
                fg="red",
                bold=True,
            )
            raise click.Abort()
        elif isinstance(err, httpx.TimeoutException):
            click.secho(
                (
                    "Request to iDAQ timed out\n\n"
                    "Verify that your computer's only internet connection is to the iDAQ"
                ),
                fg="red",
                bold=True,
            )
            raise click.Abort()
        else:
            # Shouldn't get here but catch just in case
            raise click.Abort(f"Unhandled HTTP error: {err}")

    return html


@click.version_option(version="0.1")
@click.command()
@click.option("--dlall", "-a", is_flag=True)
@click.option("--dlpath", "-p", type=Path)
def cli(dlall: bool, dlpath: Path) -> None:
    base_url = httpx.URL(r"http://192.168.1.2/")
    logs_url = base_url.copy_with(path="/logs.cgi")
    html = get_logs_page(logs_url)

    log_files = parse_iDAQ_log_page(html, base_url)
    if log_files:
        click.clear()
        click.echo("Available Log Files:")
        for idx, log in enumerate(log_files):
            click.echo(f"{idx+1}. {log}")

        if not dlall:
            click.secho("\nSelect log file(s) to download", fg="green")
            click.secho(
                "Request multiple files with a comma separated list (e.g. 2, 3, 4)", fg="green"
            )
            logs_to_download = click.prompt("?").split(",")
            log_dl_idx = [int(idx) - 1 for idx in logs_to_download]
        else:
            click.secho("\nDownloading all log files", fg="blue")
            log_dl_idx = [idx for idx in range(len(log_files))]

        for idx in log_dl_idx:
            if not dlpath:
                dlpath = iDAQdownload(log_files[idx])
            else:
                iDAQdownload(log_files[idx], dlpath)


def parse_iDAQ_log_page(html: str, base_url: httpx.URL) -> t.List[iDAQlog]:
    """Parse the HTML from the iDAQ logs.cgi page and return a list iDAQlog objects."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.findChildren("table")[0]
    rows = table.findChildren("tr")

    logfiles = []
    log_re = re.compile(r"LOG\.\d+")
    for row in rows:
        cells = row.findChildren("td")

        logtest = re.match(log_re, cells[0].text.strip())
        if logtest:
            # Normalize unicode spaces, remove datetime comma separator & split on whitespace
            tmp = unicodedata.normalize("NFKD", cells[1].text).replace(",", "").split()
            log_url = cells[0].find("a", href=True)["href"]
            logfiles.append(
                iDAQlog(base_url, logtest.string, log_url, tmp[0], f"{tmp[1]} {tmp[2]}")
            )

    return logfiles


class DownloadProgressBar(tqdm):  # pragma: no cover
    """
    Create a download progress bar with update hook.

    From tqdm examples: https://github.com/tqdm/tqdm#hooks-and-callbacks
    """

    def update_to(
        self, n_blocks: int = 1, block_size: int = 1, total_size: t.Optional[int] = None
    ) -> None:
        """Progress bar update hook."""
        if total_size is not None:
            self.total = total_size

        self.update(n_blocks * block_size - self.n)  # Will also set self.n = b * bsize


def iDAQdownload(log_obj: iDAQlog, save_path: t.Optional[Path] = None) -> Path:
    """
    Download the iDAQ log file, represented as `iDAQlog`, to the directory specified by `save_path`.

    If no `save_path` is provided, the user is prompted to enter one.

    `save_path` is returned to allow for chaining of multiple log downloads
    """
    if not save_path:
        click.secho("Enter save path", fg="green")
        save_path = Path(click.prompt("?", default="."))

    click.secho(f"\nEnter file name for {log_obj.log_name}", fg="green")
    click.secho(f"{log_obj.extension} will be appended automatically", fg="green")
    filename = click.prompt("?", default=log_obj.log_name)

    save_fullfile = save_path.joinpath(filename + log_obj.extension)
    click.secho(f"Downloading {log_obj.log_name} to {save_fullfile} ... ", fg="blue", nl=False)

    successful = False
    try:
        with DownloadProgressBar(unit="b", unit_scale=True, miniters=1, desc=log_obj.log_name) as t:
            urlretrieve(
                str(log_obj.dl_url),
                filename=save_fullfile,
                reporthook=t.update_to,
                data=None,
            )

            successful = True
    except httpx.TimeoutException:
        click.secho("Download Failed: Timeout", fg="red", bold=True)

    if successful:
        click.secho("Done", fg="green")

    # Return save_path to allow chaining of multiple logs
    return save_path


# Add an entry point for use outside of a venv
if __name__ == "__main__":  # pragma: no cover
    cli()
