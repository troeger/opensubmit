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


def console_script():
    '''
        The main entry point for the production
        administration script 'opensubmit-exec',
        installed by setuptools.
    '''
    if len(sys.argv) == 1:
        print("opensubmit-exec [configure|run|test <dir>|unlock|help] [-c config_file]")
        exit(0)

    if "help" in sys.argv[1]:
        print("configure:        Check config files and registration of a OpenSubmit test machine.")
        print("run:              Fetch and run code to be tested from the OpenSubmit web server. Suitable for crontab.")
        print("test <dir>:       Run test script from a local folder for testing purposes.")
        print("unlock:           Break the script lock, because of crashed script.")
        print("help:             Print this help")
        print(
            "-c config_file    Configuration file to be used (default: {0})".format(CONFIG_FILE_DEFAULT))
        exit(0)

    if len(sys.argv) > 2 and sys.argv[2] == "-c":
        config_fname = sys.argv[3]
    else:
        config_fname = CONFIG_FILE_DEFAULT

    if "configure" in sys.argv[1]:
        print("Checking configuration of the OpenSubmit executor...")
        if has_config(config_fname):
            print("Config file found at " + config_fname)
            config = read_config(config_fname)
            if not check_config(config):
                exit(1)
        else:
            print("ERROR: Seems like the config file %s does not exist." %
                  config_fname)
            print("       I am creating a new one, don't forget to edit it !")
            print("       Re-run this script again afterwards.")
            if create_config(config_fname):
                print("File created.")
                exit(0)
            else:
                exit(1)

        send_hostinfo(config)
        exit(0)

    if "unlock" in sys.argv[1]:
        config = read_config(config_fname)
        break_lock(config)
        exit(0)

    if "run" in sys.argv[1]:
        config = read_config(config_fname)
        # Perform additional precautions for unattended mode in cron
        kill_longrunning(config)
        with ScriptLock(config):
            download_and_run(config)
        exit(0)

    if "test" in sys.argv[1]:
        config = read_config(config_fname)
        copy_and_run(config, sys.argv[2])
        exit(0)


if __name__ == "__main__":
    console_script()
