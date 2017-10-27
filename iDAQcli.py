import re
import shutil
import unicodedata
import urllib.parse
import urllib.request
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from socket import gethostbyname, gethostname, timeout
from sys import exit

import click
import pytz
from bs4 import BeautifulSoup

_TIMEOUT = 5  # Global timeout, seconds

@click.version_option(version='0.1')
@click.command()
@click.option('--dlall', '-a', is_flag=True)
@click.option('--dlpath', '-p')
def cli(dlall, dlpath):
    baseurl = r'http://192.168.1.2/'
    logsurl = urllib.parse.urljoin(baseurl, 'logs.cgi')
    click.secho(f'Contacting {logsurl} ...', fg='green')
    try:
        with urllib.request.urlopen(logsurl, timeout=_TIMEOUT) as request:
            html = request.read()
    except (urllib.error.URLError, timeout) as err:
        if isinstance(err, timeout) or isinstance(err.reason, timeout):
            click.secho('Request timed out\n\n'
                        'Verify that the iDAQ is connected and powered on',
                        fg='red', bold=True)
            exit(1)
        if isinstance(err, urllib.error.URLError):
            click.secho('Cannot connect to iDAQ\n\n'
                        'Verify iDAQ is connected and powered on\n'
                        'Verify ethernet adapter is configured with a static IP of 192.168.1.1',
                        fg='red', bold=True)
            exit(1)
        else:
            raise err

    # htmldump = './testpage.html'
    # with open(htmldump, 'r') as fID:
    #     html = fID.readlines()[0]
    
    logfiles = parseiDAQlog(html, baseurl)
    if logfiles:
        click.clear()
        click.echo('Available Log Files:')
        for idx, log in enumerate(logfiles):
            click.echo(f'{idx+1}. {log}')
        
        if not dlall:
            click.secho('\nSelect log file(s) to download', fg='green')
            click.secho('Request multiple files with a comma separated list (e.g. 2, 3, 4)', fg='green')
            logstodownload = click.prompt('?').split(',')
            logdlidx = [int(idx)-1 for idx in logstodownload]
        else:
            click.secho('\nDownloading all log files', fg='blue')
            logdlidx = [idx for idx in range(len(logfiles))]

        for idx in logdlidx:
            iDAQdownload(logfiles[idx], dlpath)

def parseiDAQlog(html, baseurl):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.findChildren('table')[0]
    rows = table.findChildren('tr')

    logfiles = []
    log_re = re.compile('LOG\.\d+')
    for row in rows:
        cells = row.findChildren('td')
        
        logtest = re.match(log_re, cells[0].text.strip())
        if logtest:
            # Normalize unicode spaces, remove datetime comma separator & split on whitespace
            tmp = unicodedata.normalize('NFKD', cells[1].text).replace(',', '').split()
            logurl = cells[0].find('a', href=True)['href']
            logfiles.append(iDAQlog(baseurl, logtest.string, logurl, tmp[0], f'{tmp[1]} {tmp[2]}'))

    return logfiles

class iDAQlog():
    def __init__(self, baseurl, lognamestr, logurlstr, nbytesstr, logdatetimestr):
        self._dateformat_in  = '%Y-%m-%d %H:%M:%S'
        self._dateformat_out = '%Y-%m-%d %H:%M:%S'
        
        self.extension = '.iDAQ'
        self.baseurl = baseurl
        self.logname = lognamestr
        self.logurl = logurlstr
        self.nbytes = int(nbytesstr)
        self.logdatetime = datetime.strptime(logdatetimestr, self._dateformat_in).replace(tzinfo=pytz.utc)

    def __str__(self):
        mebibytes = self.nbytes/1048576
        return f'{self.logname:8s}{mebibytes: 7.2f} MB{self.logdatetime.strftime(self._dateformat_out):>22s}'

def iDAQdownload(logObj, savepath):
    if not savepath:
        click.secho('Enter save path', fg='green')
        savepath = Path(click.prompt('?', default='.'))

    click.secho(f'\nEnter file name for {logObj.logname}', fg='green')
    click.secho(f'{logObj.extension} will be appended automatically', fg='green')
    filename = click.prompt('?', default=logObj.logname)

    dlurl = urllib.parse.urljoin(logObj.baseurl, logObj.logurl)
    savefullfile = savepath.joinpath(filename + logObj.extension)
    click.secho(f'Downloading {logObj.logname} to {savefullfile} ... ', fg='blue', nl=False)

    try:
        successful = False
        with ExitStack() as stack:
            response = urllib.request.urlopen(dlurl, timeout=_TIMEOUT)
            fID = open(savefullfile, 'wb')
            
            shutil.copyfileobj(response, fID)
            successful = True
    except (urllib.error.URLError, timeout) as err:
        if isinstance(err, timeout) or isinstance(err.reason, timeout):
           click.secho('Download Failed: Timeout', fg='red', bold=True)
    
    if successful:
        click.secho('Done', fg='green')

# # Add an entry point for use outside of a venv
if __name__ == '__main__':
    cli()
