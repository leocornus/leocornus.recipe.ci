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

  >>> from fabric.operations import local
  >>> from fabric.context_managers import lcd

Create the working folder and the build folder.
We should have the absolute path for both.
::

  >>> import os
  >>> test_folder = tmpdir('test')
  >>> build_folder = tmpdir('builds')

We will use angular-trac-client repository for testing.
::

  >>> repo_url = 'https://github.com/leocornus/angular-trac-client.git'

get ready the working folder.
::

  >>> with lcd(test_folder):
  ...     clone = local('git clone %s' % repo_url, True)
  [localhost] local: git clone ...
  >>> prj_folder = os.path.join(test_folder, 'angular-trac-client')

Get the most recent 10 commits for testing.
::

  >>> with lcd(prj_folder):
  ...     local('git pull', True)
  ...     ids = local('git log --format=%h -10 .', True)
  [localhost] local: git pull
  'Already up-to-date.'
  [localhost] local: git log ...
  >>> commit_ids = ids.splitlines()
  >>> len(commit_ids)
  10

Prepare a buildlog.
We will save 5 of the commits in build log.
::

  >>> logdata = ""
  >>> for i in range(6):
  ...     logdata = logdata + '%s-%s\n' % (i + 1, commit_ids[9 - i])
  >>> write(prj_folder, '.buildlog', logdata)
  >>> print(logdata)
  1-...
  2-...
  3-...
  4-...
  5-...
  6-...

The file .buildlog will have the content like following::

  1-00f7247
  2-cbca861
  3-60667b1
  4-6df2a6e
  5-80fc8b4
  6-55a916b

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
  ... """ % dict(prj_folder=prj_folder, builds_folder=build_folder))
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
  ...

Tear down
---------

The **buildoutTearDown** should clean up temp directories.
