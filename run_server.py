#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

run_mv_server.py is a module for use on a computer running MultiVu.  It can
be used with MultiPyVu.MultiVuClient to control a Quantum Desing cryostat.

"""

import sys

from MultiPyVu import MultiVuServer as mvs


def server(flags: str = ''):
    '''
    This method deciphers the command line text, and the instantiates the
    MultiVuServer.

    Parameters
    ----------
    flags : str, optional
        The default is ''.

    Returns
    -------
    None.

    '''

    user_flags = []
    if flags == '':
        user_flags = sys.argv[1:]
    else:
        user_flags = flags.split(' ')

    s = mvs.MultiVuServer(user_flags, keep_server_open=True)
    s.open()


if __name__ == '__main__':
    server()
