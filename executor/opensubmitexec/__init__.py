'''
    OpenSubmit executor functionality.

    This library has two parts: The validator support functions and the
    daemon functionality for fetching and running validator scripts.

    You should add a cron job for the following call:
       python3 -m opensubmitexec.cmdline

    For writing test scripts, check the manual at open-submit.org
'''

# The default location of the config file for the executor
CONFIG_FILE_DEFAULT='/etc/opensubmit/executor.ini'

