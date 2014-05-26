#!/usr/bin/env python

"""
Main module for maxify command line application.
"""

import argparse

import colorama

from maxify.repo import Repository
from maxify.log import enable_loggers
from maxify.ui import MaxifyCmd


def main():
    parser = argparse.ArgumentParser(description="Maxify programmer time "
                                                 "tracker client")
    parser.add_argument("-p",
                        "--project",
                        help="Name of project to start tracking time against "
                             "once the client starts. For a project belonging "
                             "to a particular organization, prefix the name "
                             "with the organization, like: scopetastic/maxify.")
    parser.add_argument("-f",
                        "--data-file",
                        default="maxify.db",
                        help="Path to Maxify data file. By default, this is "
                             "'maxify.db' in the current directory.")
    parser.add_argument("-x",
                        "--debug",
                        action="store_true",
                        help="Print debugging statements during execution.")
    parser.add_argument("command",
                        nargs=argparse.REMAINDER,
                        help="Optional command to execute at startup and then "
                             "exit.")

    args = parser.parse_args()

    if args.debug:
        enable_loggers()

    colorama.init()
    Repository.init(args.data_file)

    interpreter = MaxifyCmd()
    interpreter.cmdloop(args)


if __name__ == "__main__":
    main()
