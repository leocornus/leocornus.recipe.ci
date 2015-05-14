# __init__.py

import os
import logging
from fabric.operations import local
from fabric.context_managers import lcd
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

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
        last_build_id, \
        last_commit_id = self.get_buildlog(working_folder)
        log.info("Last build id %s" % last_build_id)
        log.info("Last commit id %s" % last_commit_id)

        # find the build id and commit id we will working on.
        build_id = int(last_build_id) + 1
        total_pending, \
        commit_id = self.get_next_commit_id(working_folder, 
                                            last_commit_id)
        if total_pending == 0:
            # now new commit! return.
            log.info("No new commit found!")
            return []

        log.info('Total number of commits pending build %s' % 
                 total_pending)
        log.info('Next commit to build %s-%s' % (build_id, commit_id))

        # update build log.
        self.update_buildlog(working_folder, build_id, commit_id)

        commit_detail = self.get_commit_detail(working_folder, 
                                               commit_id)
        log.info('Repository Remote: %s' % commit_detail[0])
        log.info('Repository Branch: %s' % commit_detail[1])
        log.info('Project Folder: %s' % commit_detail[2])

        # fetch the subfolder using the sparse checkout
        # execute test script.
        # preparing the test result
        # write to wiki page.
        build_folder = self.sparse_checkout(builds_folder, build_id, 
                                            commit_id, commit_detail)
        log.info('Get ready build folder: %s' % build_folder)
        result = self.execute_tests(build_folder)
        log.info('Result: %s' % result)

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
            log = local('echo %s-%s > .buildlog' % 
                        (build_id, commit_id), True)

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
            pull = local('git pull', True)
            ids = local('git log %s %s .' % (format, since), True)

        if not ids:
            # now new commit found.
            return (0, -1)
        else:
            ids = ids.splitlines()
            total = len(ids)
            next = ids[total - 1]
            return (total, next)

    # try to get the remote and subfolder
    def get_commit_detail(self, working_folder, commit_id):
        """return the remote url and the subfolder for the 
        given commit id.
        """

        log_option = '--name-only --format=%h -1'
        with lcd(working_folder):
            remote = local('git remote -v', True)
            branch = local('git branch', True)
            changeset = local('git log %s %s' % 
                              (log_option, commit_id), True)
        # get the remote url:
        remote = remote.splitlines()[0]
        remote = remote.strip().split()[1]
        # the branch name:
        branch = branch.split()[1]
        # subfolder for sparse checkout.
        change_file = changeset.strip().splitlines()[2]
        folders = change_file.split(os.sep)
        subfolder = os.path.join(folders[0], folders[1])

        return (remote, branch, subfolder)

    # git sparse checkout.
    def sparse_checkout(self, builds_folder, build_id, commit_id,
                        commit_detail):
        """sparse checkout for the given commit.
        """

        # make the build folder.
        build_folder = os.path.join(builds_folder, str(build_id))
        os.mkdir(build_folder)

        remote, branch, subfolder = commit_detail

        # git sparse checkout based on commit detail.
        with lcd(build_folder):
            r = local('git init >> log', True)
            r = local('git remote add -f %s %s >> log' % 
                      ('origin', remote), True)
            r = local('git config core.sparsecheckout true >> log', 
                      True)
            r = local('echo %s/ >> .git/info/sparse-checkout' %
                      subfolder, True)
            r = local('git pull origin %s >> log' % branch, True)
            r = local('git checkout %s >> log' % commit_id, True)
            #r = local('ls -la %s/%s/..' % (build_folder, subfolder), 
            #          False)

        return os.path.join(build_folder, subfolder)

    # execute tests in the given build_folder.
    def execute_tests(self, build_folder, cicfg=".cicfg"):
        """analyze the test scripts from file .cicfg
        execute test scripts and return the test result.
        If no file .cicfg present, skip the build.
        """
        scripts = self.get_test_scripts(build_folder, cicfg)
        if not scripts:
            # skip test.
            return "No test script specified, SKIP!"

        with lcd(build_folder):
            for script in scripts:
                # save teh result in .log file.
                r = local('%s >> .log' % script, True)

        # read the .log as result.
        log_file = os.path.join(build_folder, '.log')
        f = open(log_file, 'r')
        test_results = f.read()

        return test_results

    # find out the test scripts.
    def get_test_scripts(self, build_folder, cicfg):
        """return all test scripts in a list.
        """

        cfg_file = os.path.join(build_folder, cicfg)
        if not os.path.exists(cfg_file):
            # try to find the config file fron user folder.
            home_folder = os.path.expanduser("~")
            cfg_file = os.path.join(home_folder, cicfg)
        config = configparser.ConfigParser()
        cfg_file = config.read(cfg_file)
        if config.has_option('ci', 'script'):
            scripts = config.get('ci', 'script')
            scripts = scripts.strip().splitlines()
        else:
            scripts = []

        return scripts
