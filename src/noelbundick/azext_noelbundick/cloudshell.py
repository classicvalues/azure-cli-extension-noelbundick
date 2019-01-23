import json
import operator
import os
import re
import requests
import shutil
import subprocess
import sys
import tarfile

from azure.cli.core.api import get_config_dir
from azure.cli.core.commands import CliCommandType
from knack.log import get_logger

logger = get_logger(__name__)


def load_command_table(self, _):
    custom = CliCommandType(operations_tmpl='{}#{{}}'.format(__name__))

    with self.command_group('shell', custom_command_type=custom) as g:
        g.custom_command('ssh', 'launch_cloudshell')


def load_arguments(self, _):
    pass


def get_latest_azssh():
    platform = sys.platform

    r = requests.get('https://api.github.com/repos/noelbundick/azssh/releases')
    releases = r.json()

    releases = sorted(releases, key=lambda x: x['published_at'], reverse=True)
    latest = (x['browser_download_url'] for x in releases[0]['assets'])
    download = next(x for x in latest if platform in x)
    return download


def launch_cloudshell():
    is_current = False
    
    latest_azssh = get_latest_azssh()
    azssh = os.path.join(get_config_dir(), 'azssh')

    if os.path.isfile(azssh):
        match = re.search('https://github.com/noelbundick/azssh/releases/download/v(?P<version>.*)/(.*).tar.gz', latest_azssh)
        latest_version = match.group('version')
        current_version = subprocess.check_output([azssh, 'version']).decode("utf-8").strip()

        logger.info('Current azssh: {}, Latest azssh: {}'.format(current_version, latest_version))
        if latest_version == current_version:
            is_current = True
    
    if not is_current:
        logger.warn('Downloading latest azssh from {}'.format(latest_azssh))
        tarball = os.path.join(get_config_dir(), 'azssh.tar.gz')
        r = requests.get(latest_azssh, allow_redirects=True, stream=True)
        with open(tarball, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

        logger.warn('Extracting tarball: {}'.format(tarball))
        with tarfile.open(tarball) as f:
            f.extractall(path=get_config_dir())

    logger.warn('Launching Azure Cloud Shell, type `exit` to disconnect')
    os.system(azssh)