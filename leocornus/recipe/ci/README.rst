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
  >>> prj_folder = os.path.join(prj_folder, 'app')

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

Prepare a buildlog
~~~~~~~~~~~~~~~~~~

The buildlog will have only one line to track the last build id and commit id.
::

  >>> logdata = "%s-%s" % (100, commit_ids[5])
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
::

  >>> home_folder = os.path.expanduser("~")
  >>> print(home_folder)
  >>> ci_scripts = """
  ... [ci]
  ... script:
  ...   ls -la
  ... """
  >>> write(home_folder, '.cicfg', ci_scripts)

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
  test-ci: Save Builds 0
  test-ci: Last build id 100
  test-ci: Last commit id ...
  [localhost] local: git log ...
  test-ci: Total number of commits pending build 5
  test-ci: Next commit to build 101-...
  [localhost] local: echo 101-... > .buildlog
  [localhost] local: git remote -v
  [localhost] local: git branch
  [localhost] local: git log --name-only --format=%h -1 ...
  test-ci: Repository Remote: https://github.com/leocornus/angular-trac-client.git
  test-ci: Repository Branch: master
  test-ci: Project Folder: app/...
  [localhost] local: ...
  test-ci: Get ready build folder: .../builds/101
  ...

Tear down
---------

The **buildoutTearDown** should clean up temp directories.

clean the .cicfg file.
::

  >>> remove = local('rm -rf %s' % cicfg, True)
  [localhost] local: rm -rf ...
