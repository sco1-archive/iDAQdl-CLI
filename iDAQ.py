import click
from sys import exit
from datetime import datetime
import pytz
import urllib.request
import urllib.parse
from socket import timeout
from bs4 import BeautifulSoup
import re
import unicodedata
import shutil
from pathlib import Path
from contextlib import ExitStack

@click.version_option(version='0.1')
@click.command()
@click.option('--dlall', '-a', is_flag=True)
def cli(dlall):
    baseurl = r'http://192.168.1.2/'
    logsurl = urllib.parse.urljoin(baseurl, 'logs.cgi')
    click.secho(f'Contacting {logsurl} ...', fg='green')
    try:
        with urllib.request.urlopen(logsurl, timeout=5) as request:
            html = request.read()
    except urllib.error.URLError as err:
        if isinstance(err.reason, timeout):
            click.secho('Request timed out\n\nVerify that the iDAQ is connected and powered on', fg='red', bold=True)
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

            click.secho('Enter save path', fg='green')
            dlpath = Path(click.prompt('?', default='.'))
        else:
            logdlidx = [idx for idx in range(len(logfiles))]
            dlpath = Path('.')  # Use current directory for now

        for idx in logdlidx:
            click.secho('\nDownloading all log files', fg='blue')
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

        self.baseurl = baseurl
        self.logname = lognamestr
        self.logurl = logurlstr
        self.nbytes = int(nbytesstr)
        self.logdatetime = datetime.strptime(logdatetimestr, self._dateformat_in).replace(tzinfo=pytz.utc)

    def __str__(self):
        mebibytes = self.nbytes/1048576
        return f'{self.logname:8s}{mebibytes: 7.2f} MB{self.logdatetime.strftime(self._dateformat_out):>22s}'

def iDAQdownload(logObj, savepath):
    click.secho(f'\nEnter file name for {logObj.logname}', fg='green')
    filename = click.prompt('?', default=logObj.logname + '.iDAQ')

    dlurl = urllib.parse.urljoin(logObj.baseurl, logObj.logurl)
    savefullfile = savepath.joinpath(filename)
    click.secho(f'Downloading {logObj.logname} to {savefullfile} ... ', fg='blue', nl=False)

    try:
        successful = False
        with ExitStack() as stack:
            response = urllib.request.urlopen(dlurl, timeout=3)
            fID = open(savefullfile, 'wb')
            
            shutil.copyfileobj(response, fID)
            successful = True
    except urllib.error.URLError as err:
        if isinstance(err.reason, timeout):
           click.secho('Download Failed: Timeout', fg='red', bold=True)
    
    if successful:
        click.secho('Done', fg='green')