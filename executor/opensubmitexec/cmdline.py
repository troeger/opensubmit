# Administration script functionality on the production system

import sys

from . import CONFIG_FILE_DEFAULT
from .server import fetch_job, fake_fetch_job, send_hostinfo
from .running import kill_longrunning
from .locking import ScriptLock, break_lock
from .config import read_config, has_config, create_config, check_config


def download_and_run(config):
    '''
    Main operation of the executor.

    Returns True when a job was downloaded and executed.
    Returns False when no job could be downloaded.
    '''
    job = fetch_job(config)
    if job:
        job._run_validate()
        return True
    else:
        return False


def copy_and_run(config, src_dir):
    '''
    Local-only operation of the executor.
    Intended for validation script developers,
    and the test suite.

    Please not that this function only works correctly
    if the validator has one of the following names:
        - validator.py
        - validator.zip

    Returns True when a job was prepared and executed.
    Returns False when no job could be prepared.
    '''
    job = fake_fetch_job(config, src_dir)
    if job:
        job._run_validate()
        return True
    else:
        return False


def get_config_fname(argv):
    for index, entry in enumerate(argv):
        if entry == "-c":
            return argv[index + 1]
    return CONFIG_FILE_DEFAULT


def console_script():
    '''
        The main entry point for the production
        administration script 'opensubmit-exec',
        installed by setuptools.
    '''
    if len(sys.argv) == 1:
        print("opensubmit-exec [configcreate <server_url>|configtest|run|test <dir>|unlock|help] [-c config_file]")
        return 0

    if "help" in sys.argv[1]:
        print("configcreate <server_url>:  Create initial config file for the OpenSubmit executor.")
        print("configtest:                 Check config file for correct installation of the OpenSubmit executor.")
        print("run:                        Fetch and run code to be tested from the OpenSubmit web server. Suitable for crontab.")
        print("test <dir>:                 Run test script from a local folder for testing purposes.")
        print("unlock:                     Break the script lock, because of crashed script.")
        print("help:                       Print this help")
        print(
            "-c config_file    Configuration file to be used (default: {0})".format(CONFIG_FILE_DEFAULT))
        return 0

    # Translate legacy commands
    if sys.argv[1] == "configure":
        sys.argv[1] = 'configtest'

    config_fname = get_config_fname(sys.argv)

    if "configcreate" in sys.argv[1]:
        print("Creating config file at " + config_fname)

        server_url = sys.argv[2]

        if create_config(config_fname, override_url=server_url):
            print("Config file created, fetching jobs from " + server_url)
            return 0
        else:
            return 1

    if "configtest" in sys.argv[1]:
        print("Testing config file at " + config_fname)

        if has_config(config_fname):
            config = read_config(config_fname)
            if not check_config(config):
                return 1
        else:
            print("ERROR: Seems like the config file %s does not exist. Call 'opensubmit-exec configcreate <server_url>' first." %
                  config_fname)
            return 1

        print("Sending host information update to server ...")
        send_hostinfo(config)
        return 0

    if "unlock" in sys.argv[1]:
        config = read_config(config_fname)
        break_lock(config)
        return 0

    if "run" in sys.argv[1]:
        config = read_config(config_fname)
        # Perform additional precautions for unattended mode in cron
        kill_longrunning(config)
        with ScriptLock(config):
            download_and_run(config)
        return 0

    if "test" in sys.argv[1]:
        config = read_config(config_fname)
        copy_and_run(config, sys.argv[2])
        return 0


if __name__ == "__main__":
    exit(console_script())
