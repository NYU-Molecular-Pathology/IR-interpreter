#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for running rsync between directories, used with monitor to deal with remote directories
"""
import json
import subprocess as sp

config = {
'sourceDir': "input",
'targetDir': 'output'
}

def load_config(input_json = "rsync.json"):
    """
    Updates the module's internal ``config`` dictionary based on values in supplied JSON file

    Parameters
    ----------
    input_json: str
        path to JSON formatted file to update module config
    """
    with open(input_json) as f:
        d = json.load(f)
    config.update(d)

def rsync_args(source, target, flags = ('-vzhrP',), dryRun = False, swap = False):
    """
    Generates args to use for running ``rsync`` on the local system.

    Parameters
    ----------
    source: str
        Path to source directory to copy data from
    target: str
        Path to target directory to copy data to
    flags: list
        a list of character strings representing flags to be used with ``rsync``
    dryRun: bool
        whether or not to include the ``--dry-run`` arg for ``rsync``
    swap: bool
        wether or not to swap the order of ``source`` and ``target`` arguments, effectively reversing the sync direction.

    Returns
    -------
    list
        a list of character strings representing the arguments to be used for a system call to ``rsync``

    Notes
    -----
    Uses values stored in module's internal ``config`` dictionary.

    """
    # base arg
    args = ['rsync']
    # add flags
    for item in flags:
        args.append(item)
    # add dry run
    if dryRun:
        args.append('--dry-run')
    # if a server is set, include more flags
    if config.get('targetServer') or config.get('sourceServer'):
        args.append('-e')
        args.append('"ssh"')
    # if server was passed, update source and target args
    if config.get('targetServer'):
        targetArg = config['targetServerUsername'] + '@' + config['targetServer'] + ':' + target
    else:
        targetArg = target
    if config.get('sourceServer'):
        sourceArg = config['sourceServerUsername'] + '@' + config['sourceServer'] + ':' + target
    else:
        sourceArg = source
    # if swap was set, reverse order of source and target args
    if swap is True:
        args.append(targetArg)
        args.append(sourceArg)
    else:
        args.append(sourceArg)
        args.append(targetArg)
    return(args)

def rsync(source, target, dryRun = True, swap = False):
    """
    Makes a system call to ``rsync`` to copy files and directories between locations.

    Parameters
    ----------
    source: str
        Path to source directory to copy data from
    target: str
        Path to target directory to copy data to
    dryRun: bool
        whether or not to include the ``--dry-run`` arg for ``rsync``
    swap: bool
        wether or not to swap the order of ``source`` and ``target`` arguments, effectively reversing the sync direction.

    """
    args = rsync_args(source = source, target = target, dryRun = dryRun, swap = swap)
    cmd = ' '.join(args)
    print(cmd)
    # rsync -vzheR --copy-links --progress -e "ssh" --files-from="$server_file_list" ${server_info}:/results/analysis/output/Home/ "${outdir}"
    process = sp.Popen(args, stdout = sp.PIPE, stderr = sp.PIPE, universal_newlines = True)
    proc_stdout, proc_stderr = process.communicate()
    proc_stdout = proc_stdout.strip()
    proc_stderr = proc_stderr.strip()
    print(proc_stdout)
    print(proc_stderr)
