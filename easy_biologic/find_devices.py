#!/usr/bin/env python
# coding: utf-8

# # Find Devices
# Convenience script for finding Biologic devices.

# In[13]:


import argparse

from .lib import ec_find as ecf


# In[5]:


def run():
    # parse command line
    parser = argparse.ArgumentParser(
        description = 'Find BioLogic devices.'
    )

    parser.add_argument( 
        '--connection', '-conn', '-c',
        dest = 'conn',
        choices = [ 'usb', 'eth' ],
        action = 'store',
        help = 'The type of connection to use.'
    )

    args = parser.parse_args()

    # find and display devices
    devs = ecf.find_devices( args.conn )
    for device in devs:
        desc = '{}: {}'.format(
            device.kind,
            device.connection_string
        )

        print( desc )


# In[ ]:


if __name__ == '__main__':
    run()

