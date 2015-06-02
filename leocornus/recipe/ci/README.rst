.. contents:: Table of Contents
   :depth: 5

Explain the story here.

What's the story
----------------

Continuous Integration (CI) testing for small and medium projects.


Preparing the case
------------------

Import modules.
::

  >>> import pexpect
  >>> import shlex
  >>> from subprocess import check_output

Create the working folder and the build folder.
We should have the absolute path for both.
::

  >>> import os
  >>> test_folder = tmpdir('test')
  >>> build_folder = tmpdir('builds')

We will use the leocornus demo repository 
**leocornus-ci-projects** for testing.
::

  >>> repo_url = 'https://github.com/leocornus/leocornus-ci-projects.git'

get ready the working folder.
::

  >>> os.chdir(test_folder)
  >>> clone = pexpect.run('git clone %s' % repo_url)
  >>> prj_folder = os.path.join(test_folder, 'leocornus-ci-projects')

Get the most recent 5 commits for testing.
::

  >>> os.chdir(prj_folder)
  >>> pull = pexpect.run('git pull')
  >>> git_log = 'git log --format=%h -5 .'
  >>> ids = check_output(shlex.split(git_log))
  >>> #print(ids)
  >>> commit_ids = ids.splitlines()
  >>> len(commit_ids)
  5

Prepare a buildlog
~~~~~~~~~~~~~~~~~~

The buildlog will have only one line to track the last build id 
and commit id.
We will use the number 2 commit as an example for the last build.
The first entry of the git log is the lastest commit by default.
So we will only build the latest commit.
::

  >>> logdata = "%s-%s" % (100, commit_ids[1])
  >>> write(prj_folder, '.buildlog', logdata)
  >>> print(logdata)
  100-...

The file .buildlog will have the content like following::

  100-80fc8b4

Prepare a cicfg
~~~~~~~~~~~~~~~

the **.cicfg** will be searched from the following location:

- project folder, while user could customize it by project.
- user's home folder **~/.cicfg**, it will be override by the 
  same file in project folder.

We will use the .cicfg file in suer's home folder for testing.
The method **expanduser** in build testing context will return
a temporary folder.
We will not test this for now.
::

  ...>>> home_folder = os.path.expanduser("~")
  ...>>> print(home_folder)
  ...>>> ci_scripts = """
  ...... [ci]
  ...... script:
  ......   ls -la
  ...... """
  ...>>> write(home_folder, '.cicfg', ci_scripts)

Prepare a mwrc file
~~~~~~~~~~~~~~~~~~~

Get ready a sample mwrc file for testing.
We will save the mwrc file in working folder.
::

  >>> rc_file = os.path.join(prj_folder, '.mwrc')
  >>> mwrc = open(rc_file, 'w')
  >>> cfg_data = """
  ... [mwclient]
  ... update_wiki = no
  ... host = mediawiki.site.com
  ... path = /wiki/
  ... username = seanchen
  ... password = password
  ... 
  ... [wiki page]
  ... title: Project:CI/Builds/%(build_id)s-%(commit_id)s
  ... comment: build log for commit %(commit_id)s
  ... content: 
  ...   %(build_status)s
  ...   ===Commit===
  ...   <div>%(commit_message)s</div>
  ...   ===Build Log===
  ...   <div>%(build_log)s</div>
  ... """
  >>> mwrc.write(cfg_data)
  >>> mwrc.close()

Set up the ci buildout
----------------------

Get ready a buildout to execute CI testing.
::

  >>> write(sample_buildout, 'buildout.cfg',
  ... """
  ... [buildout]
  ... parts = test-ci
  ...
  ... [test-ci]
  ... recipe = leocornus.recipe.ci
  ... working-folder = %(prj_folder)s
  ... builds-folder = %(builds_folder)s
  ... wiki-rc-file = %(rc_file)s
  ... """ % dict(prj_folder=prj_folder, builds_folder=build_folder,
  ...            rc_file=rc_file))
  >>> ls(sample_buildout)
  d bin
  - buildout.cfg
  d develop-eggs
  d eggs
  d parts

Execute the buildout
--------------------

run the buildout::

  >>> os.chdir(sample_buildout)
  >>> print(system(buildout))
  Installing test-ci.
  test-ci: Working Folder ...
  test-ci: Builds Folder ...
  test-ci: Save Builds 0
  test-ci: Last build id 100
  test-ci: Last commit id ...
  test-ci: Total number of commits pending build 1
  test-ci: Next commit to build 101-...
  test-ci: Repository Remote: https://github.com/...
  test-ci: Repository Branch: master
  test-ci: Project Folder: projects/...
  test-ci: Get ready build folder: .../builds/101/...
  test-ci: Execute test script: npm test
  test-ci: Result: Build success!
  test-ci: Convert build log to HTML.
  test-ci: Wiki page title: Project:CI/Builds/101-...
  test-ci: Wiki update is OFF
  ...

buildout won't store those Fabric local output.
::

  [localhost] local: git pull
  [localhost] local: git log ...
  test-ci: Total number of commits pending build 1
  test-ci: Next commit to build 101-...
  [localhost] local: echo 101-... > .buildlog
  [localhost] local: git remote -v
  [localhost] local: git branch
  [localhost] local: git log --name-only --format=%h -1 ...
  test-ci: Repository Remote: https://github.com/leocornus/leocourns-ci-projects.git
  test-ci: Repository Branch: master
  test-ci: Project Folder: projects/...
  [localhost] local: echo projects/...
  test-ci: Get ready build folder: .../builds/101/...
  test-ci: Result: Build success!
  ...

explore the build log
---------------------

Read the build log.
::

  >>> log_file = '%s/101.log' % build_folder
  >>> blog = open(log_file)
  >>> logs = blog.read()
  >>> #print(logs)
  >>> 'git init' in logs
  True

quick test for converting build log
::

  >>> from subprocess import Popen
  >>> from subprocess import check_output
  >>> from subprocess import PIPE
  >>> cat = Popen(['cat', log_file], stdout=PIPE)
  >>> html_log = check_output(['aha', '-b', '--no-header'], stdin=cat.stdout)
  >>> #print(html_log)
  >>> 'color:lime' in html_log
  True

Tear down
---------

The **buildoutTearDown** should clean up temp directories.

clean the .cicfg file.
::

  ...>>> remove = local('rm -rf %s' % cicfg, True)
  ...[localhost] local: rm -rf ...
