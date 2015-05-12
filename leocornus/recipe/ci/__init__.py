# __init__.py

import os
import logging
from fabric.operations import local
from fabric.context_managers import lcd

__author__ = "Sean Chen"
__email__ = "sean.chen@leocorn.com"

class CiRecipe:
    """The entry point for leocornus.recipe.ci
    """

    # buildout recipe's constructor,
    # buildout will use this to create a recipe instance.
    def __init__(self, buildout, name, options):

        self.options = options
        # part's name.
        self.name = name
        self.buildout = buildout

        # set default value of options.
        self.options.setdefault('working-folder', 
                                '/usr/ci/projects')
        self.options.setdefault('builds-folder',
                                '/usr/ci/builds')

    # install method.
    def install(self):
        """Will be executed when install
        """

        log = logging.getLogger(self.name)
        log.info("Working Folder %s" % 
                 self.options.get('working-folder'))
        log.info("Builds Folder %s" %
                 self.options.get('builds-folder'))
        pass

    # update method.
    def update(self):
        """Will be executed when update...
        """
        pass
