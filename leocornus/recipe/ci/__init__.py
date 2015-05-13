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
        self.options.setdefault('save-builds', '0')

    # install method.
    def install(self):
        """Will be executed when install
        """

        log = logging.getLogger(self.name)
        working_folder = self.options.get('working-folder')
        builds_folder = self.options.get('builds-folder')
        save_builds = self.options.get('save-builds')
        log.info("Working Folder %s" % working_folder)
        log.info("Builds Folder %s" % builds_folder)
        log.info("Save Builds %s" % save_builds)

        # get last commit from buildlog
        last_build_id, last_commit_id = self.get_buildlog(working_folder)
        log.info("Last build id %s" % last_build_id)
        log.info("Last commit id %s" % last_commit_id)

        # find the build id and commit id we will working on.
        build_id = int(last_build_id) + 1
        total_pending, commit_id = self.get_next_commit_id(working_folder, 
                                                           last_commit_id)
        log.info('Total number of commits pending build %s' % total_pending)
        log.info('Next commit to build %s-%s' % (build_id, commit_id))

        # update build log.
        self.update_buildlog(working_folder, build_id, commit_id)

        return []

    # update method.
    def update(self):
        """Will be executed when update...
        """
        pass

    # return the build log
    def get_buildlog(self, working_folder):
        """return build log in a tuple with the pattern
        (BUILD_ID, COMMIT_ID)
        """

        log_file = os.path.join(working_folder, '.buildlog')
        if os.path.exists(log_file):
            log = open(log_file, 'r').read().splitlines()
        else:
            # if no build log exists, we will start from first commit.
            log = ['0-0']

        return log[0].split("-")

    def update_buildlog(self, working_fodler, build_id, commit_id):
        """update build log with new build id and commit id.
        """

        with lcd(working_fodler):
            log = local('echo %s-%s > .buildlog' % (build_id, commit_id), True)

    # return the next commit for build.
    def get_next_commit_id(self, working_folder, last_commit_id):
        """return the next commit id for build.
        (total number of commits, next commit)
        """

        # we only need the short sha key
        format = '--format=%h'
        if last_commit_id == "0":
            since = ""
        else:
            since = "%s.." % last_commit_id
        with lcd(working_folder):
            ids = local('git log %s %s .' % (format, since), True)

        if not ids:
            # now new commit found.
            return (0, -1)
        else:
            ids = ids.splitlines()
            total = len(ids)
            next = ids[total - 1]
            return (total, next)
