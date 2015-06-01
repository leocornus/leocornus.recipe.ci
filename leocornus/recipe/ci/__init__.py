# __init__.py

import os
import logging
from subprocess import check_call
from subprocess import Popen
from subprocess import PIPE
from subprocess import check_output
from subprocess import CalledProcessError
import shlex
from fabric.operations import local
from fabric.context_managers import lcd
import mwclient
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
        self.options.setdefault('wiki-rc-file', '~/.mwrc')

    # install method.
    def install(self):
        """Will be executed when install
        """

        log = logging.getLogger(self.name)
        working_folder = self.options.get('working-folder')
        builds_folder = self.options.get('builds-folder')
        mwrc = self.options.get('wiki-rc-file')
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

        # preparing a log file to track the whole build process from
        # this step.
        build_log_file = os.path.join(builds_folder, 
                                      '%s.log' % build_id)
        self.build_log = open(build_log_file, 'w')

        # fetch the subfolder using the sparse checkout
        # execute test script.
        build_folder, returncode = self.sparse_checkout(builds_folder, build_id, 
                                            commit_id, commit_detail)
        log.info('Get ready build folder: %s' % build_folder)
        returncode, result = self.execute_tests(build_folder)
        log.info('Result: %s' % result)
        self.build_log.close()

        # convert build log to html  
        # This depends on aha
        cat = Popen(['cat', build_log_file], stdout=PIPE)
        html_log = check_output(['aha', '-b', '--no-header'], stdin=cat.stdout)
        # replace white space to &nbsp; to keep the format on wiki page
        html_log = html_log.replace('  ', '&nbsp;&nbsp;')
        log.info('Convert build log to HTML.')
        log_file = open(build_log_file)
        html_log = log_file.read()

        # save the html as a wiki page
        page_values = {
          'commit_id' : commit_id,
          'commit_message' : commit_detail[3],
          'build_id' : build_id,
          'build_status' : result,
          'build_log' : html_log
        }
        self.save_to_wiki(mwrc, page_values)

        return []

    # update method.
    def update(self):
        """Will be executed when update...
        """
        self.install()

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
            name_status = local('git log --name-status -1 %s' %
                                commit_id, True)
        # get the remote url:
        remote = remote.splitlines()[0]
        remote = remote.strip().split()[1]
        # the branch name:
        branch = branch.split()[1]
        # subfolder for sparse checkout.
        change_file = changeset.strip().splitlines()[2]
        folders = change_file.split(os.sep)
        subfolder = os.path.join(folders[0], folders[1])

        return (remote, branch, subfolder, name_status)

    def call_cmd(self, cmd, separator='-', logging=True):
        """utility method to log and execute a script
        """
        if(logging):
            out = self.build_log
            err = self.build_log
        else:
            out = None
            err = None

        # write to build log by using echo.
        check_call(['echo', ''], stdout=out, stderr=err)
        check_call(['echo', cmd], stdout=out, stderr=err)
        line = separator * len(cmd)
        check_call(['echo', line], stdout=out, stderr=err)
        check_call(['echo', ''], stdout=out, stderr=err)
        check_call(shlex.split(cmd), stdout=out, stderr=err)

    # git sparse checkout.
    def sparse_checkout(self, builds_folder, build_id, commit_id,
                        commit_detail):
        """sparse checkout for the given commit.
        """

        # make the build folder.
        build_folder = os.path.join(builds_folder, str(build_id))
        os.mkdir(build_folder)

        remote, branch, subfolder, name_status = commit_detail
        returncode = 0

        # git sparse checkout based on commit detail.
        os.chdir(build_folder)
        try:
            self.call_cmd('git init', logging=True)

            cmd = 'git remote add -f %s %s' % ('origin', remote)
            self.call_cmd(cmd, logging=False)

            cmd = 'git config core.sparsecheckout true'
            self.call_cmd(cmd, logging=False)
        
            cmd = 'echo %s/ >> .git/info/sparse-checkout' % subfolder
            #self.build_log.writelines([cmd, '\n'])
            r = local(cmd, True)

            cmd = 'git pull origin %s' % branch
            self.call_cmd(cmd, logging=False)

            cmd = 'git checkout %s' % commit_id
            self.call_cmd(cmd, logging=True)

            cmd = 'git config url."https://".insteadof git://'
            self.call_cmd(cmd, logging=False)
        except CalledProcessError as cpe:
            returncode = cpe.returncode

        return (os.path.join(build_folder, subfolder), returncode)

    # execute tests in the given build_folder.
    def execute_tests(self, build_folder, cicfg=".cicfg"):
        """analyze the test scripts from file .cicfg
        execute test scripts and return the test result.
        If no file .cicfg present, skip the build.
        """

        log = logging.getLogger(self.name)
        scripts = self.get_test_scripts(build_folder, cicfg)
        if not scripts:
            # skip test.
            return "No test script specified, SKIP!"

        returncode = 0

        # TODO: update to return fail or success only,
        # based on return code!
        os.chdir(build_folder)
        try:
            for script in scripts:
                # save all results in .log file.
                #r = local('%s >> .log' % script, False)
                log.info('Execute test script: %s' % script)
                self.call_cmd(script)
        except CalledProcessError as cpe:
            returncode = cpe.returncode

        if(returncode > 0):
            test_results = 'Build failed!'
        else:
            test_results = 'Build success!'

        return (returncode, test_results)

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

    # save to wiki
    def save_to_wiki(self, mwrc, values):
        """save build log as a wiki page
        """

        log = logging.getLogger(self.name)
        if os.path.exists(mwrc):
            # read wiki site information from the resource file
            rc = configparser.ConfigParser()
            file_name = rc.read(mwrc)
            mw_info = dict(rc.items('mwclient'))
            # set raw to True for page fields
            mw_page = dict(rc.items('wiki page', True))

            # get ready the wiki page
            title = mw_page['title'] % values
            content = mw_page['content'] % values
            comment = mw_page['comment'] % values
            log.info('Wiki page title: %s' % title)

            # save to wiki site
            if not mw_info.has_key('update_wiki'):
                # update_wiki not set, give the default value.
                mw_info['update_wiki'] = 'no'

            # 
            if mw_info['update_wiki'] == 'yes':
                # try to create the mwclient site instance.
                site = mwclient.Site(mw_info['host'], 
                                     path=mw_info['path'])
                site.login(mw_info['username'], 
                           mw_info['password'])

                # create new page. 
                thepage = site.Pages[title]
                ret = thepage.save(content, comment)
                # logging
                log.info('Wiki update: %(result)s' % ret)
            else:
                # logging
                log.info('Wiki update is OFF')
        else:
            log.info('No mwrc file set up, skip wiki update!')
