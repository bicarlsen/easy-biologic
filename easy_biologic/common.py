import os
import re
import json
import pkg_resources
from glob import glob


def technique_directory( version = None ):
    """
    :param version: Techniques version or None to use default.
        [Default: None]
    :returns: Path to techniques resource directory.
    """
    if version is None:
        # get default version
        version = default_techniques_version()

    tdir = f'techniques-{version}'
    rdir = pkg_resources.resource_filename( 'easy_biologic', tdir )

    return rdir


def default_techniques_version():
    """
    :returns: Default version of techniques.
    """
    version_file = pkg_resources.resource_filename(
        'easy_biologic',
        'techniques_version.json'
    )

    try:
        with open( version_file ) as vf:
            info = json.load( vf )
            default_version = info[ 'version' ]

    except Exception as err:
        # version file could not be loaded
        # attempt to find manually

        # get technique directories
        # DANGER: Relies on this file being at same level as technique folders.
        # TODO [1]: Make finding root dir more robust.
        _root_dir = os.path.normpath( os.path.join( __file__, '..' ) )
        tech_dirs = [
            tdir
            for tdir in glob( os.path.join( _root_dir, 'techniques-*' ) )
            if os.path.isdir( tdir )
        ]

        # parse versions
        version_pattern = 'techniques\-([\d\.]+)'
        versions = []
        for tdir in tech_dirs:
            match = re.match( version_pattern, os.path.basename( tdir ) )
            if match is None:
                # error in matching
                # all directories should match pattern
                raise RuntimeError( f'Invalid technique directory {tdir}' )

            version = match.group( 1 )
            versions.append( version )

        versions.sort()
        if len( versions ) < 1:
            # could not find any technique directories
            raise RuntimeError( 'Could not find any valid technique directories.' )

        default_version = versions[ -1 ]

    return default_version 


