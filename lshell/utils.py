#
#    Limited command Shell (lshell)
#  
#    Copyright (C) 2008-2013 Ignace Mouzannar (ghantoos) <ghantoos@ghantoos.org>
#
#    This file is part of lshell
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import subprocess
import sys
import platform
import os

try:
    from os import urandom
except:
    def urandom(n):
        try:
            _urandomfd = open("/dev/urandom", 'r')
        except Exception,e:
            print e
            raise NotImplementedError("/dev/urandom (or equivalent) not found")
        bytes = ""
        while len(bytes) < n:
            bytes += _urandomfd.read(n - len(bytes))
        _urandomfd.close()
        return bytes

ld_preload = ''

def get_aliases(line, aliases):
    """ Replace all configured aliases in the line
    """

    for item in aliases.keys():
        reg1 = '(^|;|&&|\|\||\|)\s*%s([ ;&\|]+|$)(.*)' % item
        reg2 = '(^|;|&&|\|\||\|)\s*%s([ ;&\|]+|$)' % item

        # in case aliase bigin with the same command
        # (this is until i find a proper regex solution..)
        aliaskey = urandom(10)

        while re.findall(reg1, line):
            (before, after, rest) = re.findall(reg1, line)[0]
            linesave = line
            cmd = "%s %s" % (item, rest)

            line = re.sub(reg2, "%s %s%s" % (before, aliaskey,       \
                                                     after), line, 1)

            # if line does not change after sub, exit loop
            if linesave == line:
                break

        # replace the key by the actual alias
        line = line.replace(aliaskey, aliases[item])

    for char in [';']:
        # remove all remaining double char
        line = line.replace('%s%s' %(char, char), '%s' %char)
    return line

def get_noexec(noexec=''):
  """ Get the sudo noexec file path, if available. This will allow us to prevent
      applications from executing random commands thus escaping the shell
  """

  if sys.platform.startswith('freebsd'):
    noexec = '/usr/local/libexec/sudo_noexec.so'
  elif sys.platform.startswith('netbsd'):
    noexec = '/usr/pkg/libexec/sudo_noexec.so'
  elif sys.platform.startswith('linux'):
    if platform.linux_distribution(full_distribution_name=0)[0] in ('centos',
                                                                    'redhat'):
      noexec = '/usr/libexec/sudo_noexec.so'

    elif platform.linux_distribution(full_distribution_name=0)[0] in ('fedora'):
      noexec = '/usr/libexec/sudo/sudo_noexec.so'
    elif platform.linux_distribution(full_distribution_name=0)[0] in ('debian',
                                                                      'ubuntu',
                                                                      'SuSE'):
      noexec = '/usr/lib/sudo/sudo_noexec.so'

  if os.path.isfile(noexec):
    return 'LD_PRELOAD=%s' % noexec
  else:
    return 'LD_PRELOAD='

def exec_cmd(cmd):
  """ execute a command, locally catching the signals """

  # set LD_PRELOAD= if not already set (do it only once)
  global ld_preload
  if not ld_preload:
    ld_preload = get_noexec()

  try:
    retcode = subprocess.call("%s %s" % (ld_preload, cmd), shell=True)
  except KeyboardInterrupt:
    # exit code for user terminated scripts is 130
    retcode = 130

  return retcode
