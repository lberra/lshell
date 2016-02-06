import unittest

import lshell
from lshell.shellcmd import ShellCmd, LshellTimeOut
from lshell.checkconfig import CheckConfig
from lshell.utils import get_aliases, get_noexec
import os

TOPDIR="%s/../" % os.path.dirname(os.path.realpath(__file__))

class TestFunctions(unittest.TestCase):
  args = ['--config=%s/etc/lshell.conf' % TOPDIR, "--quiet=1"]
  userconf = CheckConfig(args).returnconf()
  shell = ShellCmd(userconf, args)

  def test_checksecure_doublequote(self):
    """ quoted text should not be forbidden """
    INPUT = 'ls -E "1|2" tmp/test'
    return self.assertEqual(self.shell.check_secure(INPUT), 0)

  def test_checksecure_simplequote(self):
    """ quoted text should not be forbidden """
    INPUT = "ls -E '1|2' tmp/test"
    return self.assertEqual(self.shell.check_secure(INPUT), 0)

  def test_checksecure_doublepipe(self):
    """ double pipes should be allowed, even if pipe is forbidden """
    args = self.args + ["--forbidden=['|']"]
    userconf = CheckConfig(args).returnconf()
    shell = ShellCmd(userconf, args)
    INPUT = "ls || ls"
    return self.assertEqual(shell.check_secure(INPUT), 0)

  def test_checksecure_forbiddenpipe(self):
    """ forbid pipe, should return 1 """
    args = self.args + ["--forbidden=['|']"]
    userconf = CheckConfig(args).returnconf()
    shell = ShellCmd(userconf, args)
    INPUT = "ls | ls"
    return self.assertEqual(shell.check_secure(INPUT), 1)

  def test_checksecure_forbiddenchar(self):
    """ forbid character, should return 1 """
    args = self.args + ["--forbidden=['l']"]
    userconf = CheckConfig(args).returnconf()
    shell = ShellCmd(userconf, args)
    INPUT = "ls"
    return self.assertEqual(shell.check_secure(INPUT), 1)

  def test_checksecure_sudo_command(self):
    """ quoted text should not be forbidden """
    INPUT = "sudo ls"
    return self.assertEqual(self.shell.check_secure(INPUT), 1)

  def test_checksecure_notallowed_command(self):
    """ forbidden command, should return 1 """
    args = self.args + ["--allowed=['ls']"]
    userconf = CheckConfig(args).returnconf()
    shell = ShellCmd(userconf, args)
    INPUT = "ll"
    return self.assertEqual(shell.check_secure(INPUT), 1)

  def test_checkpath_notallowed_path(self):
    """ forbidden command, should return 1 """
    args = self.args + ["--path=['/home', '/var']"]
    userconf = CheckConfig(args).returnconf()
    shell = ShellCmd(userconf, args)
    INPUT = "cd /tmp"
    return self.assertEqual(shell.check_path(INPUT), 1)

  def test_checkpath_notallowed_path_completion(self):
    """ forbidden command, should return 1 """
    args = self.args + ["--path=['/home', '/var']"]
    userconf = CheckConfig(args).returnconf()
    shell = ShellCmd(userconf, args)
    INPUT = "cd /tmp/"
    return self.assertEqual(shell.check_path(INPUT, completion=1), 1)

  def test_checkpath_dollarparenthesis(self):
    """ when $() is allowed, return 0 if path allowed """
    args = self.args + ["--forbidden=[';', '&', '|','`','>','<', '${']"]
    userconf = CheckConfig(args).returnconf()
    shell = ShellCmd(userconf, args)
    INPUT = "echo $(echo aze)"
    return self.assertEqual(shell.check_path(INPUT), 0)

  def test_checkconfig_configoverwrite(self):
    """ forbid ';', then check_secure should return 1 """
    args = ['--config=%s/etc/lshell.conf' % TOPDIR, '--strict=123']
    userconf = CheckConfig(args).returnconf()
    return self.assertEqual(userconf['strict'], 123)

  def test_overssh(self):
    """ test command over ssh """
    args = self.args + ["--overssh=['exit']", '-c exit']
    os.environ['SSH_CLIENT'] = '8.8.8.8 36000 22'
    if os.environ.has_key('SSH_TTY'):
      os.environ.pop('SSH_TTY')
    with self.assertRaises(SystemExit) as cm:
      userconf = CheckConfig(args).returnconf()
    return self.assertEqual(cm.exception.code, 0)

  def test_multiple_aliases_with_separator(self):
    """ multiple aliases using &&, || and ; separators """
    # enable &, | and ; characters
    aliases={'foo':'foo -l', 'bar':'open'}
    INPUT = "foo; fooo  ;bar&&foo  &&   foo | bar||bar   ||     foo"
    return self.assertEqual(get_aliases(INPUT, aliases),
              ' foo -l; fooo  ; open&& foo -l  && foo -l | open|| open   || foo -l')

  def test_sudo_all_commands_expansion(self):
    """ sudo_commands set to 'all' should be equal to allowed variable """
    args = self.args + ["--sudo_commands=all"]
    userconf = CheckConfig(args).returnconf()
    # exclude internal and sudo(8) commands
    exclude = ['exit','lpath','lsudo','history','clear','export','sudo']
    allowed = [x for x in userconf['allowed'] if x not in exclude]
    # sort lists to compare
    userconf['sudo_commands'].sort()
    allowed.sort()
    return self.assertEqual(allowed, userconf['sudo_commands'])

  def test_noexec_ld_preload(self):
    """ LD_PRELOAD should not be empty when tested on known machines """
    args = self.args
    userconf = CheckConfig(args).returnconf()
    ld_preload = get_noexec()
    return self.assertIn('LD_PRELOAD=/usr',ld_preload)

if __name__ == "__main__":
    unittest.main()
