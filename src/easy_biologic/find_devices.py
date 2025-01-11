#!/usr/bin/env python
# coding: utf-8

import argparse

from .lib import ec_find as ecf


def run():
    """Find connected BioLogic devices.

    Use: From a terminal run `python -m easy_biologic.find_devices`.
    """
    # parse command line
    parser = argparse.ArgumentParser(description="Find BioLogic devices.")

    parser.add_argument(
        "--connection",
        "-conn",
        "-c",
        dest="conn",
        choices=["usb", "eth"],
        action="store",
        help="The type of connection to use.",
    )

    args = parser.parse_args()

    # find and display devices
    devs = ecf.find_devices(args.conn)
    for device in devs:
        desc = "{}: {}".format(device.kind, device.connection_string)

        print(desc)


if __name__ == "__main__":
    run()
