#!/home/shengwei/anaconda3/bin/python

import csv
import errno
import getpass
import locale
import os
import platform
import time
import shlex
import socket
import sys
import tempfile
import urllib3

from optparse import OptionParser, OptionGroup, SUPPRESS_HELP
from re import compile, escape, sub
from subprocess import Popen, call, PIPE, STDOUT

try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

fsli_C_FAILED = 1
fsli_C_OK = 2
fsli_C_SKIP = 4
fsli_C_WARN = 3
CURRENT = 0
UPDATE = 1
UPGRADE = 2
BOURNE_SHELLS = ('sh', 'bash', )


def memoize(f):
    cache = f.cache = {}

    def g(*args, **kwargs):
        key = (f, tuple(args), frozenset(kwargs.items()))
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]
    return g


class InstallError(Exception):
    pass


class ShellColours(object):
    default = '\033[0m'
    rfg_kbg = '\033[91m'
    gfg_kbg = '\033[92m'
    yfg_kbg = '\033[93m'
    mfg_kbg = '\033[95m'
    yfg_bbg = '\033[104;93m'
    bfg_kbg = '\033[34m'
    bold = '\033[1m'


class MsgUser(object):
    __debug = False
    __quiet = False

    @classmethod
    def debug_on(cls):
        cls.__debug = True

    @classmethod
    def debug_off(cls):
        cls.__debug = False

    @classmethod
    def quiet_on(cls):
        cls.__quiet = True

    @classmethod
    def quiet_off(cls):
        cls.__quiet = False

    @classmethod
    def is_quiet(cls):
        return cls.__quiet

    @classmethod
    def is_debug(cls):
        return cls.__debug

    @classmethod
    def debug(cls, message, newline=True):
        if cls.__debug:
            mess = str(message)
            if newline:
                mess += "\n"
            sys.stderr.write(mess)

    @classmethod
    def message(cls, msg):
        if cls.__quiet:
            return
        print(msg)

    @classmethod
    def question(cls, msg):
        print(msg)

    @classmethod
    def skipped(cls, msg):
        if cls.__quiet:
            return
        print("".join(
            (ShellColours.mfg_kbg, "[Skipped] ", ShellColours.default, msg)))

    @classmethod
    def ok(cls, msg):
        if cls.__quiet:
            return
        print("".join(
            (ShellColours.gfg_kbg, "[OK] ", ShellColours.default, msg)))

    @classmethod
    def failed(cls, msg):
        print("".join(
            (ShellColours.rfg_kbg, "[FAILED] ", ShellColours.default, msg)))

    @classmethod
    def warning(cls, msg):
        if cls.__quiet:
            return
        print("".join(
            (ShellColours.bfg_kbg,
             ShellColours.bold,
             "[Warning]",
             ShellColours.default, " ", msg)))


class ProgressBar(object):
    def __init__(self, x=0, y=0, mx=1, numeric=False, percentage=False):
        self.x = x
        self.y = y
        self.width = 50
        self.current = 0
        self.max = mx
        self.numeric = numeric
        self.percentage = percentage

    def update(self, reading):
        if MsgUser.is_quiet():
            return
        percent = int(round(reading * 100.0 / self.max))
        cr = '\r'
        if not self.numeric and not self.percentage:
            bar = '#' * int(percent)
        elif self.numeric:
            bar = "/".join(
                (str(reading),
                 str(self.max))) + ' - ' + str(percent) + "%\033[K"
        elif self.percentage:
            bar = "%s%%" % (percent)
        sys.stdout.write(cr)
        sys.stdout.write(bar)
        sys.stdout.flush()
        self.current = percent
        if percent == 100:
            sys.stdout.write(cr)
            if not self.numeric and not self.percentage:
                sys.stdout.write(" " * int(percent))
                sys.stdout.write(cr)
                sys.stdout.flush()
            elif self.numeric:
                sys.stdout.write(" " * (len(str(self.max))*2 + 8))
                sys.stdout.write(cr)
                sys.stdout.flush()
            elif self.percentage:
                sys.stdout.write("100%")
                sys.stdout.write(cr)
                sys.stdout.flush()


def temp_file_name(mode='r', close=False):
    """Return a name for a temporary file - uses mkstemp to create the file and
    returns a tuple (file object, file name).
    Opens as read-only unless mode specifies otherwise. If close is set to True
    will close the file before returning.
    The file object is a fdopen file object so lacks a useable file name."""
    (tmpfile, fname) = tempfile.mkstemp()
    file_obj = os.fdopen(tmpfile, mode)

    if close:
        file_obj.close()
    return file_obj, fname


class RunCommandError(Exception):
    pass


def run_cmd_dropstdout(command, as_root=False):
    """Run the command and return result."""
    command_line = shlex.split(command)

    if as_root and os.getuid() != 0:
        try:
            sudo_pwd = get_sudo_pwd()
        except SudoPasswordError:
            raise RunCommandError(
                "Unable to get valid administrator's password")
        command_line.insert(0, '-S')
        command_line.insert(0, 'sudo')
    else:
        sudo_pwd = ''
    try:
        cmd = Popen(command_line, stdin=PIPE, stdout=None, stderr=PIPE)
        if sudo_pwd:
            cmd.stdin.write(sudo_pwd + '\n')
            cmd.stdin.flush()
        (_, error) = cmd.communicate()
    except Exception:
        raise
    if cmd.returncode:
        MsgUser.debug("An error occured (%s, %s)" % (cmd.returncode, error))
        raise RunCommandError(error)


def run_cmd(command, as_root=False):
    """Run the command and return result."""
    command_line = shlex.split(command)

    if as_root and os.getuid() != 0:
        try:
            sudo_pwd = get_sudo_pwd()
        except SudoPasswordError:
            raise RunCommandError(
                "Unable to get valid administrator's password")
        command_line.insert(0, '-S')
        command_line.insert(0, 'sudo')
    else:
        sudo_pwd = ''
    MsgUser.debug("Will call %s" % command_line)
    try:
        cmd = Popen(command_line, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        if sudo_pwd:
            cmd.stdin.write(sudo_pwd + '\n')
            cmd.stdin.flush()
        (output, error) = cmd.communicate()
    except Exception:
        raise
    if cmd.returncode:
        MsgUser.debug("An error occured (%s, %s)" % (cmd.returncode, error))
        raise RunCommandError(error)
    MsgUser.debug("Command completed successfully (%s)" % output)
    return output


def run_cmd_displayoutput(command, as_root=False):
    """Run the command and display output."""
    command_line = shlex.split(command)

    if as_root and os.getuid() != 0:
        try:
            sudo_pwd = get_sudo_pwd()
        except SudoPasswordError:
            raise RunCommandError(
                "Unable to get valid administrator's password")

        command_line.insert(0, '-S')
        command_line.insert(0, 'sudo')
        MsgUser.debug("Will call %s" % command_line)
        cmd = Popen(
            command_line,
            stdin=PIPE, stdout=sys.stdout, stderr=sys.stderr)
        if sudo_pwd:
            cmd.stdin.write(sudo_pwd + '\n')
            cmd.stdin.flush()
        cmd.communicate()
        return_code = cmd.returncode
    else:
        return_code = call(command_line)

    if return_code:
        MsgUser.debug("An error occured (%s)" % return_code)
        raise RunCommandError(return_code)
    MsgUser.debug("Command completed successfully")


def check_sudo(sudo_pwd):
    command_line = ['sudo', '-S', 'true']
    MsgUser.debug("Checking sudo password")
    cmd = Popen(
        command_line,
        stdin=PIPE,
        stdout=DEVNULL,
        stderr=DEVNULL
    )
    cmd.stdin.write(sudo_pwd + '\n')
    cmd.stdin.flush()
    cmd.communicate()

    if cmd.returncode != 0:
        return False
    else:
        return True


class SudoPasswordError(Exception):
    pass


@memoize
def get_sudo_pwd():
    """Get the sudo password from the user"""
    MsgUser.message("We require your password to continue...")
    attempts = 0
    valid = False

    while attempts < 3 and not valid:
        sudo_pwd = getpass.getpass('password: ')
        valid = check_sudo(sudo_pwd)
        if not valid:
            MsgUser.failed("Incorrect password")
        attempts += 1
    if not valid:
        raise SudoPasswordError()
    return sudo_pwd


class DeletionRefused(Exception):
    pass


class SafeDeleteError(Exception):
    pass


def safe_delete(fs_object, as_root=False):
    """Delete file/folder, becoming root if necessary.
    Run some sanity checks on object"""

    banned_items = ['/', '/usr', '/usr/bin', '/usr/local', '/bin',
                    '/sbin', '/opt', '/Library', '/System', '/System/Library',
                    '/var', '/tmp', '/var/tmp', '/lib', '/lib64', '/Users',
                    '/home', '/Applications', '/private', '/etc', '/dev',
                    '/Network', '/net', '/proc']
    if os.path.isdir(fs_object):
        del_opts = "-rf"
    else:
        del_opts = '-f'

    if fs_object in banned_items:
        raise DeletionRefused('Will not delete %s!' % fs_object)

    command_line = " ".join(('rm', del_opts, fs_object))
    try:
        result = run_cmd(command_line, as_root)
    except RunCommandError as e:
        raise SafeDeleteError(str(e))
    return result


class MoveError(Exception):
    pass


def move(source, target, as_root):
    try:
        run_cmd_dropstdout(" ".join(('mv', source, target)), as_root)
    except RunCommandError as e:
        raise MoveError(str(e))


class IsDirectoryError(Exception):
    pass


class CopyFileError(Exception):
    pass


def copy_file(fname, destination, as_root):
    """Copy a file using sudo if necessary"""
    MsgUser.debug("Copying %s to %s (as root? %s)" % (
        fname, destination, as_root))
    if os.path.isdir(fname):
        raise IsDirectoryError('Source (%s) is a director!' % fname)

    if os.path.isdir(destination):
        # Ensure that copying into a folder we have a terminating slash
        destination = destination.rstrip('/') + "/"
    copy_opts = '-p'
    command_line = " ".join(('cp', copy_opts, fname, destination))
    try:
        result = run_cmd(command_line, as_root)
    except RunCommandError as e:
        raise CopyFileError(str(e))
    return result


def file_contains(fname, search_for):
    """Equivalent of grep"""
    regex = compile(escape(search_for))
    found = False
    MsgUser.debug("In file_contains.")
    MsgUser.debug("Looking for %s in %s." % (search_for, fname))

    f = open(fname, 'r')
    for l in f:
        if regex.search(l):
            found = True
            break
    f.close()

    return found


def file_contains_1stline(fname, search_for):
    """Equivalent of grep - returns first occurrence"""
    regex = compile(escape(search_for))
    found = ''
    MsgUser.debug("In file_contains_1stline.")
    MsgUser.debug("Looking for %s in %s." % (search_for, fname))
    f = open(fname, 'r')
    for l in f:
        if regex.search(l):
            found = l
            break
    f.close()

    return found


def line_string_replace(line, search_for, replace_with):
    return sub(escape(search_for), escape(replace_with), line)


def line_starts_replace(line, search_for, replace_with):
    if line.startswith(search_for):
        return replace_with + '\n'
    return line


class MoveFileError(Exception):
    pass


def move_file(from_file, to_file, requires_root=False):
    """Move a file, using /bin/cp via sudo if requested.
    Will work around known bugs in python."""

    if requires_root:
        try:
            run_cmd_dropstdout(" ".join(
                ("/bin/cp", from_file, to_file)), as_root=True)
        except RunCommandError as e:
            MsgUser.debug(e)
            raise MoveFileError("Failed to move %s (%s)" % (from_file, str(e)))
        os.remove(from_file)
    else:
        try:
            move(from_file, to_file, requires_root)
        except OSError as e:
            # Handle bug in some python versions on OS X writing to NFS home
            # folders, Python tries to preserve file flags but NFS can't do
            # this. It fails to catch this error and ends up leaving the file
            # in the original and new locations!
            if e.errno == 45:
                # Check if new file has been created:
                if os.path.isfile(to_file):
                    # Check if original exists
                    if os.path.isfile(from_file):
                        # Destroy original and continue
                        os.remove(from_file)
                else:
                    try:
                        run_cmd_dropstdout("/bin/cp %s %s" % (
                                from_file, to_file), as_root=False)
                    except RunCommandError as e:
                        MsgUser.debug(e)
                        raise MoveFileError("Failed to copy from %s (%s)" % (
                                from_file, str(e)))
                    os.remove(from_file)
            else:
                raise
        except Exception:
            raise


class EditFileError(Exception):
    pass


def edit_file(fname, edit_function, search_for, replace_with, requires_root):
    """Search for a simple string in the file given and replace
        it with the new text"""
    try:
        (tmpfile, tmpfname) = temp_file_name(mode='w')
        src = open(fname)

        for line in src:
            line = edit_function(line, search_for, replace_with)
            tmpfile.write(line)
        src.close()
        tmpfile.close()

        try:
            move_file(tmpfname, fname, requires_root)
        except MoveFileError as e:
            MsgUser.debug(e)
            os.remove(tmpfname)
            raise EditFileError("Failed to edit %s (%s)" % (fname, str(e)))
    except IOError as e:
        MsgUser.debug(e.strerror)
        raise EditFileError("Failed to edit %s (%s)" % (fname, str(e)))
    MsgUser.debug("Modified %s (search %s; replace %s)." % (
        fname, search_for, replace_with))


class AddToFileError(Exception):
    pass


def add_to_file(fname, add_lines, requires_root):
    """Add lines to end of a file"""
    if isinstance(add_lines, str):
        add_lines = add_lines.split('\n')
    try:
        (tmpfile, tmpfname) = temp_file_name(mode='w')
        src = open(fname)

        for line in src:
            tmpfile.write(line)
        src.close()
        tmpfile.write('\n')
        for line in add_lines:
            tmpfile.write(line)
            tmpfile.write('\n')
        tmpfile.close()
        try:
            move_file(tmpfname, fname, requires_root)

        except MoveFileError as e:
            os.remove(tmpfname)
            MsgUser.debug(e)
            raise AddToFileError("Failed to add to file %s (%s)" % (
                    fname, str(e)))
    except IOError as e:
        MsgUser.debug(e.strerror + tmpfname + fname)
        raise AddToFileError("Failed to add to file %s" % fname)
    MsgUser.debug("Modified %s (added %s)" % (fname, '\n'.join(add_lines)))


class CreateFileError(Exception):
    pass


def create_file(fname, lines, requires_root):
    """Create a new file containing lines given"""
    if isinstance(lines, str):
        lines = lines.split('\n')
    try:
        (tmpfile, tmpfname) = temp_file_name(mode='w')

        for line in lines:
            tmpfile.write(line)
            tmpfile.write('\n')
        tmpfile.close()
        try:
            move_file(tmpfname, fname, requires_root)
        except CreateFileError as e:
            os.remove(tmpfname)
            MsgUser.debug(e)
            raise CreateFileError("Failed to edit %s (%s)" % (fname, str(e)))
    except IOError as e:
        MsgUser.debug(e.strerror)
        raise CreateFileError("Failed to create %s" % (fname))
    MsgUser.debug("Created %s (added %s)" % (fname, '\n'.join(lines)))


class UnsupportedOs(Exception):
    pass


class Host(object):
    """Work out which platform we are running on"""
    o_s = platform.system().lower()
    arch = platform.machine()
    applever = ''
    os_type = os.name
    supported = True

    if o_s == 'linux':
        vendor = platform.platform().lower()
        glibc = platform.libc_ver()[1]
    else:
        supported = False

    if arch == 'x86_64':
        bits = '64'


def is_writeable(location):
    """Check if we can write to the location given"""
    writeable = True
    try:
        tfile = tempfile.NamedTemporaryFile(mode='w+b', dir=location)
        tfile.close()
    except OSError as e:
        if e.errno == errno.EACCES or e.errno == errno.EPERM:
            writeable = False
        else:
            raise
    return writeable


def is_writeable_as_root(location):
    """Check if sudo can write to a given location"""
    # This requires us to use sudo

    (f, fname) = temp_file_name(mode='w')
    f.write("FSL")
    f.close()

    result = False
    tmptarget = '/'.join((location, os.path.basename(fname)))
    MsgUser.debug(" ".join(('/bin/cp', fname, tmptarget)))
    try:
        run_cmd_dropstdout(" ".join(('/bin/cp',
                                     fname, tmptarget)), as_root=True)
        result = True
        os.remove(fname)
        run_cmd_dropstdout(" ".join(('/bin/rm',
                                     '-f', tmptarget)), as_root=True)
    except RunCommandError as e:
        MsgUser.debug(e)
        os.remove(fname)
        result = False
    MsgUser.debug("Writeable as root? %s" % result)
    return result


class ChecksumCalcError(Exception):
    pass


def sha256File(filename, bs=1048576):
    """Returns the sha256 sum of the given file."""
    MsgUser.message("Checking FSL package")
    try:
        import hashlib
        f = open(filename, 'rb')
        pb = ProgressBar(mx=os.path.getsize(filename), percentage=True)
        pb.position = 0
        fhash = hashlib.sha256()
        data = f.read(bs)
        while len(data) == bs:
            fhash.update(data)
            data = f.read(bs)
            pb.position += len(data)
            pb.update(pb.position)
        fhash.update(data)
        f.close()
        return fhash.hexdigest()
    except ImportError:
        # No SHA256 support on python pre-2.5 so call the OS to do it.
        try:
            result = run_cmd(" ".join(('sha256sum', '-b', filename)))
            return parsesha256sumfile(result)
        except RunCommandError as e:
            MsgUser.debug("SHA256 calculation error %s" % (str(e)))
            raise ChecksumCalcError


def parsesha256sumfile(sha256string):
    """Returns sha256 sum extracted from the output of sha256sum or shasum -a
    256 from OS X/Linux platforms"""
    (sha256, _) = sha256string.split("*")
    return sha256.strip()


def md5File(filename, bs=1048576):
    """Returns the MD5 sum of the given file."""
    MsgUser.message("Checking FSL package")
    try:
        import hashlib
        fhash = hashlib.md5()
    except ImportError:
        import md5
        fhash = md5.new()
    f = open(filename, 'rb')
    pb = ProgressBar(mx=os.path.getsize(filename), percentage=True)
    pb.position = 0
    data = f.read(bs)
    while len(data) == bs:
        fhash.update(data)
        data = f.read(bs)
        pb.position += len(data)
        pb.update(pb.position)
    fhash.update(data)
    f.close()
    return fhash.hexdigest()


def file_checksum(filename, chktype='sha256'):
    if chktype == 'sha256':
        return sha256File(filename)
    if chktype == 'md5':
        return md5File(filename)
    else:
        raise ChecksumCalcError('Unrecognised checksum type')


class OpenUrlError(Exception):
    pass


def open_url(url, start=0, timeout=20):
    socket.setdefaulttimeout(timeout)
    MsgUser.debug("Attempting to download %s." % url)

    try:
        http = urllib3.PoolManager()
        req = http.request('GET', url)
        if start != 0:
            req.headers['Range'] = 'bytes=%s-' % start
    except urllib3.exceptions.HTTPError as e:
        MsgUser.debug("%s HTTPError" % url)
        raise OpenUrlError("Cannot find file %s on server. "
                           "Try again later." % url)
    except urllib3.exceptions.RequestError as e:
        raise OpenUrlError(
            "Cannot find %s. Try again later." % url)
    except socket.timeout as e:
        MsgUser.debug(e)
        raise OpenUrlError("Failed to contact FSL web site. Try again later.")
    return req


class DownloadFileError(Exception):
    pass


def download_file(url, localf, timeout=20):
    """Get a file from the url given storing it in the local file specified"""

    try:
        rf = open_url(url, 0, timeout)
    except OpenUrlError as e:
        raise DownloadFileError(str(e))

    metadata = rf.info()
    rf_size = int(metadata.getheaders("Content-Length")[0])

    dl_size = 0
    block = 16384
    x = 0
    y = 0
    pb = ProgressBar(x, y, rf_size, numeric=True)

    for attempt in range(1, 6):
        # Attempt download 5 times before giving up
        pause = timeout
        try:
            try:
                lf = open(localf, 'ab')
            except Exception:
                raise DownloadFileError("Failed to create temporary file.")

            while True:
                buf = rf.read(block)
                if not buf:
                    break
                dl_size += len(buf)
                lf.write(buf)
                pb.update(dl_size)
            lf.close()
        except (IOError, socket.timeout) as e:
            MsgUser.debug(e.strerror)
            MsgUser.message("\nDownload failed re-trying (%s)..." % attempt)
            pause = 0
        if dl_size != rf_size:
            time.sleep(pause)
            MsgUser.message("\nDownload failed re-trying (%s)..." % attempt)
            try:
                rf = open_url(url, dl_size, timeout)
            except OpenUrlError as e:
                MsgUser.debug(e)
        else:
            break
    if dl_size != rf_size:
        raise DownloadFileError("Failed to download file.")


def build_url_with_protocol(protocol, base, parts):
    part_l = [protocol + '://' + base.strip('/')]
    part_l.extend([x.strip('/') for x in parts])
    return '/'.join(part_l)


def build_url(parts):
    part_l = [parts[0].strip('/')]
    part_l.extend([x.strip('/') for x in parts[1:]])
    return '/'.join(part_l)


class SiteNotResponding(Exception):
    pass

# Concept:
# Web app creates the following files:
# fslmirrorlist.txt - contains a list of mirror urls
# fslreleases.json - contains the available maps for oses
#                    mapping to a download url
# {'installer' {
#                'filename': 'fslinstaller.py',
#                'version': 'x.0.x',
#                'date': 'dd/mm/yyyy',
#                'checksum_type', 'sha256',
#                'checksum'},
#  'linux' : {
#               'centos' : {
#                   'x86_64': {
#                       '6': {
#                           'x.0.x': {
#                               'filename': 'fsl-x.0.x-centos6_64.tar.gz',
#                               'version': 'x.0.x',
#                               'date': 'dd/mm/yyyy',
#                               'checksum_type', 'sha256',
#                               'checksum': 'abf645662bcf4453235',
#                               },
#                             },
#                           },
#                         },
#              'rhel' : {'alias': 'centos'}},
# }


class GetFslDirError(Exception):
    pass


@memoize
def get_fsldir(specified_dir=None, install=False):
    """Find the installed version of FSL using FSLDIR
    or location of this script"""

    def validate_fsldir(directory):
        parent = os.path.dirname(directory)
        if parent == directory:
            raise GetFslDirError(
                "%s appears to be the root folder" %
                parent)
        if not os.path.exists(parent):
            raise GetFslDirError(
                "%s doesn't exist" %
                parent)
        if not os.path.isdir(parent):
            raise GetFslDirError(
                "%s isn't a directory" %
                parent)
        if (os.path.exists(directory) and not
                os.path.exists(os.path.join(
                        directory, 'etc', 'fslversion'
                ))):
            raise GetFslDirError(
                "%s exists and doesn't appear to be an installed FSL folder" %
                directory)

    if specified_dir:
        if install is False:
            if not check_fsl_install(specified_dir):
                raise GetFslDirError(
                        "%s isn't an 'fsl' folder" %
                        specified_dir)
        else:
            validate_fsldir(specified_dir)
        return specified_dir
    try:
        fsldir = os.environ['FSLDIR']
        try:
            validate_fsldir(fsldir)
        except GetFslDirError:
            # FSLDIR environment variable is incorrect!
            MsgUser.warning('FSLDIR environment variable '
                            'does not point at FSL install, ignoring...')
            MsgUser.debug('FSLDIR is set to %s - '
                          'this folder does not appear to exist' % (fsldir))
            fsldir = None
        else:
            fsldir = fsldir.rstrip('/')
            if MsgUser.is_quiet():
                return fsldir
    except KeyError:
        # Look to see if I'm in an FSL install
        try:
            my_parent = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))
        except NameError:
            # Running in debugger - __file__ not set, assume it's cwd
            my_parent = os.path.dirname(
                os.path.dirname(os.getcwd()))
        try:
            validate_fsldir(my_parent)
            fsldir = my_parent
        except GetFslDirError:
            fsldir = None

    if not install:
        MsgUser.debug("asking about %s" % (fsldir))
        valid_dir = False
        while not valid_dir:
            fsldir = Settings.inst_qus.ask_question(
                    'inst_loc', default=fsldir)
            try:
                validate_fsldir(fsldir)
                valid_dir = True
            except GetFslDirError as e:
                MsgUser.failed(str(e))
        return fsldir

    else:
        if not MsgUser.is_quiet():
            valid_dir = False
            while not valid_dir:
                fsldir = Settings.inst_qus.ask_question(
                    'location', default=fsldir)
                try:
                    validate_fsldir(fsldir)
                    valid_dir = True
                except GetFslDirError as e:
                    MsgUser.failed(str(e))
                    MsgUser.message(
                        """Hint - press Enter to select the default value """
                        """given in the square brackets.
If you are specifying a destination folder this needs to either be an existing
FSL install folder or a folder that doesn't already exist.""")
                    fsldir = None
        else:
            raise GetFslDirError(
                    "I can't locate FSL, try again using '-d <FSLDIR>' "
                    "to specify where to find the FSL install")
    return fsldir


def archive_version(archive):
    """Takes the path to a FSL install file
    and works out what version it is."""
    if not os.path.isfile(archive):
        raise NotAFslVersion("%s is not a file" % archive)
    else:
        # file is of form: fsl-V.V.V-platform.extensions
        (_, vstring, _) = archive.strip().split('-', 2)
        return vstring


class NotAFslVersion(Exception):
    pass


class GetInstalledVersionError(Exception):
    pass


def get_installed_version(fsldir):
    """Takes path to FSLDIR and finds installed version details"""
    MsgUser.debug("Looking for fsl in %s" % fsldir)
    v_file = os.path.join(fsldir, 'etc', 'fslversion')
    if os.path.exists(v_file):
        f = open(v_file)
        v_string = f.readline()
        f.close()
        try:
            version = v_string.strip()
        except ValueError:
            raise NotAFslVersion(
                    "%s not a valid "
                    "version string" % (v_string.strip()))
    else:
        MsgUser.debug(
                "No version information found - "
                "is this actually an FSL dir?")
        raise GetInstalledVersionError(
                "Cannot find the version information - "
                "is this actually an FSL dir?")
    MsgUser.debug("Found version %s" % (version))
    return version


def which_shell():
    return os.path.basename(os.getenv("SHELL"))


class SelfUpdateError(Exception):
    pass


class ServerFailure(Exception):
    pass


class GetInstallerError(Exception):
    pass


class ExtraDownloadError(Exception):
    pass


class ImproperlyConfigured(Exception):
    pass


class InstallInstallerError(Exception):
    pass


def install_installer(fsldir):
    """Install this script into $FSLDIR/etc"""
    targetfolder = os.path.join(fsldir, 'etc')
    as_root = False
    installer = os.path.abspath(__file__)
    MsgUser.debug(
            "Copying fslinstaller (%s) to %s" % (
                    installer,
                    targetfolder))
    if not is_writeable(targetfolder):
        if not is_writeable_as_root(targetfolder):
            raise InstallInstallerError("Cannot write to folder as root user.")
        else:
            as_root = True
    copy_file(
        installer, os.path.join(targetfolder, "fslinstaller.py"),
        as_root)


class InstallQuestions(object):
    def __init__(self):
        self.questions = {}
        self.validators = {}
        self.type = {}
        self.default = {}
        self.defaults = False

    def add_question(self, key, question, default, qtype, validation_f):
        self.questions[key] = question
        self.default[key] = default
        self.type[key] = qtype
        self.validators[key] = validation_f

    def ask_question(self, key, default=None):
        # Ask a question
        no_answer = True
        validator = self.validators[key]

        def parse_answer(q_type, answer):
            if q_type == 'bool':
                if answer.lower() == 'yes':
                    return True
                else:
                    return False
            else:
                return answer

        if not default:
            default = self.default[key]

        if self.defaults:
            MsgUser.debug(self.questions[key])
            MsgUser.debug("Automatically using the default %s" % default)
            self.answers[key] = parse_answer(self.type[key], default)
            no_answer = False

        while no_answer:
            MsgUser.question(
                "%s? %s:" % (
                    self.questions[key],
                    '[%s]' % default))
            your_answer = input()
            MsgUser.debug("Your answer was %s" % your_answer)
            if your_answer == '':
                MsgUser.debug("You want the default")
                your_answer = default
            if validator(your_answer):
                answer = parse_answer(self.type[key], your_answer)
                no_answer = False
        MsgUser.debug("Returning the answer %s" % answer)
        return answer


def yes_no(answer):
    if answer.lower() == 'y' or answer.lower() == 'n':
        return True
    else:
        MsgUser.message("Please enter y/n.")
    return False


def check_install_location(folder):
    """Don't allow relative paths"""
    MsgUser.debug("Checking %s is an absolute path" % (folder))
    if (folder == '.' or
            folder == '..' or
            folder.startswith('./') or
            folder.startswith('../') or
            folder.startswith('~')):
        MsgUser.message("Please enter an absolute path.")
        return False
    return True


def external_validate(what_to_check):
    """We will validate elsewhere"""
    return True


def check_fsl_install(fsldir):
    """Check if this folder contains FSL install"""
    MsgUser.debug("Checking %s is an FSL install" % (fsldir))
    if os.path.isdir(fsldir):
        if os.path.exists(
            os.path.join(fsldir, 'etc', 'fslversion')
        ):
            return True
    return False


def fsl_downloadname(suffix, version):
    return 'fsl-%s-%s' % (
            version, suffix)


class Settings(object):
    title = '--- FSL Installer - Version 3.0.18 equivalent ---'
    main_server = 'fsl.fmrib.ox.ac.uk'
    mirrors = [build_url_with_protocol('https',
                                       main_server, ('fsldownloads',
                                                     '')), ]
    mirrors_file = 'fslmirrorlist.txt'
    manifest_json = 'manifest.json'
    manifest_csv = 'manifest.csv'
    main_mirror = mirrors[0]
    mirror = main_mirror

    default_location = '/usr/local/fsl'
    post_inst_dir = "etc/fslconf"

    inst_qus = InstallQuestions()
    inst_qus.add_question('version_match',
                          "The requested version matches the installed "
                          "version - do you wish to re-install FSL",
                          'no', 'bool', yes_no)
    inst_qus.add_question('location',
                          "Where would you like the FSL install to be "
                          "(including the FSL folder name)",
                          default_location, 'path', check_install_location)
    inst_qus.add_question('del_old',
                          "FSL exists in the current location, "
                          "would you like to keep a backup of the old "
                          "version (N.B. You will not be able to use the old "
                          "version)",
                          'no', 'bool', yes_no)
    inst_qus.add_question('create',
                          "Install location doesn't exist, should I create it",
                          'yes', 'bool', yes_no)
    inst_qus.add_question('inst_loc',
                          "Where is the FSL folder (e.g. /usr/local/fsl)",
                          default_location, 'path', check_fsl_install)
    inst_qus.add_question('skipmd5',
                          "I was unable to download the checksum of "
                          "the install file so cannot confirm it is correct. "
                          "Would you like to install anyway",
                          'no', 'bool', yes_no)
    inst_qus.add_question('overwrite',
                          "There is already a local copy of the file, would "
                          "you like to overwrite it",
                          "yes", 'bool', yes_no)
    inst_qus.add_question('upgrade',
                          "Would you like to install upgrade",
                          "yes", 'bool', yes_no)
    inst_qus.add_question('update',
                          "Would you like to install update",
                          "yes", 'bool', yes_no)


# [ linux, centos, x86_64, 6, filename, 'fname',
#  version, 'version', date, 'date', checksum_type, 'checksum_type',
#  checksum, 'checksum', supported, 'true/false', notes, 'notes',
#  instructions, 'instructions']
# [ linux, redhat, alias, centos, supported, True/false, version, 'version' ]
# [ 'installer', filename, 'fname', version, 'version', date, 'date',
#   checksum_type, 'checksum_type', checksum, 'checksum', supported,
#   'true/false', notes, 'notes', instructions, 'instructions']
# [ feeds, filename, 'fname', version, 'version',
#   date, 'date', checksum_type, 'checksum_type', checksum, 'checksum',
#   supported, 'true/false', notes, 'notes', instructions, 'instructions']
# [ sources, filename, 'fname', version, 'version',
#   date, 'date', checksum_type, 'checksum_type', checksum, 'checksum',
#   supported, 'true/false', notes, 'notes', instructions, 'instructions']

class AutoDict(dict):
    """Automatically create a nested dict"""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value

    def freeze(self):
        """Returns a dict representation of an AutoDict"""
        frozen = {}
        for k, v in self.items():
            if type(v) == type(self):
                frozen[k] = v.freeze()
            else:
                frozen[k] = v
        return frozen


def get_csv_dict(web_url):
    MsgUser.debug("Opening "+web_url)

    try:
        url = open_url(web_url)
        manifest_reader = csv.reader(
            url, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        a_dict = AutoDict()
        for line in manifest_reader:
            MsgUser.debug(line)
            if line[0] == 'feeds':
                items = iter(line[1:])
                base_dict = dict(zip(items, items))
                a_dict[line[0]] = base_dict
            elif line[0] == 'sources':
                items = iter(line[1:])
                base_dict = dict(zip(items, items))
                a_dict[line[0]] = base_dict
            elif line[0] == 'installer':
                items = iter(line[1:])
                base_dict = dict(zip(items, items))
                a_dict[line[0]] = base_dict
            else:
                # Install package or alias
                if line[2] == 'alias':
                    items = iter(line[4:])
                    base_dict = dict(zip(items, items))
                    a_dict[
                        str(line[0])][
                            str(line[1])][
                                str(line[2])][
                                    str(line[3])] = base_dict
                else:
                    items = iter(line[5:])
                    base_dict = dict(zip(items, items))
                    MsgUser.debug(
                        ",".join(
                            (line[0], line[1], line[2], line[3], line[4])))
                    a_dict[
                        str(line[0])][
                            str(line[1])][
                                str(line[2])][
                                    str(line[3])][
                                        str(line[4])] = base_dict
    except OpenUrlError as e:
        raise ServerFailure(str(e))
    MsgUser.debug(a_dict)
    return a_dict.freeze()


class InvalidVersion(Exception):
    pass


def download_release(
        server_url=Settings.mirror, to_temp=False,
        request_version=None, skip_verify=False,
        source_code=False, feeds=False):

    version, details = server_url, request_version
    if request_version is None:
        request_version = str(version)

    if source_code or feeds:
        if source_code:
            extra_type = 'sources'
            MsgUser.message("Downloading source code")
        else:
            extra_type = 'feeds'
            MsgUser.message("Downloading FEEDS")

    MsgUser.debug(details)

    if to_temp:
        try:
            (_, local_filename) = temp_file_name(close=True)
        except Exception as e:
            MsgUser.debug("Error getting temporary file name %s" % (str(e)))
            raise DownloadError("Unable to begin download")
    else:
        local_filename = details['filename']
        if os.path.exists(local_filename):
            if os.path.isfile(local_filename):
                MsgUser.message("%s exists" % (local_filename))
                overwrite = Settings.inst_qus.ask_question('overwrite')
                if overwrite:
                    MsgUser.warning(
                        "Erasing existing file %s" % local_filename)
                    try:
                        os.remove(local_filename)
                    except Exception:
                        raise DownloadError(
                            "Unabled to remove local file %s - remove"
                            " it and try again" % local_filename)
                else:
                    raise DownloadError("Aborting download")
            else:
                raise DownloadError(
                    "There is a directory named %s "
                    "- cannot overwrite" % local_filename)

    MsgUser.debug(
            "Downloading to file %s "
            "(this may take some time)." % (local_filename))
    MsgUser.message(
            "Downloading...")

    downloaded = False
    while downloaded is False:
        try:
            file_url = '/'.join(
                (Settings.mirror.rstrip('/'), details['filename']))
            download_file(
                url=file_url,
                localf=local_filename)
            if (not skip_verify and
                (details['checksum'] !=
                    file_checksum(local_filename, details['checksum_type']))):
                raise DownloadError('Downloaded file fails checksum')
            MsgUser.ok("File downloaded")
        except DownloadFileError as e:
            MsgUser.debug(str(e))
            if Settings.mirror != Settings.main_mirror:
                MsgUser.warning(
                        "Download from mirror failed, re-trying from "
                        "main FSL download site")
                Settings.mirror = Settings.main_mirror
            else:
                raise DownloadError(str(e))
        else:
            downloaded = True
    return (local_filename, version, details)


class DownloadError(Exception):
    pass


def shell_config(shell, fsldir, skip_root=False):
    MsgUser.debug("Building environment for %s" % (shell))
    env_lines = ''

    if shell in BOURNE_SHELLS:
        if skip_root:
            env_lines += '''if [ -x /usr/bin/id ]; then
  if [ -z "$EUID" ]; then
    # ksh and dash doesn't setup the EUID environment var
    EUID=`id -u`
  fi
fi
if [ "$EUID" != "0" ]; then
'''
        env_lines += '''
# FSL Setup
FSLDIR=%s
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH
. ${FSLDIR}/etc/fslconf/fsl.sh
'''
        if skip_root:
            env_lines += '''fi'''
        match = "FSLDIR="
        replace = "FSLDIR=%s"
    elif shell == 'matlab':
        env_lines = '''
%% FSL Setup
setenv( 'FSLDIR', '%s' );
fsldir = getenv('FSLDIR');
fsldirmpath = sprintf('%%s/etc/matlab',fsldir);
path(path, fsldirmpath);
clear fsldir fsldirmpath;
'''
        match = "setenv( 'FSLDIR',"
        replace = "setenv( 'FSLDIR', '%s' );"
    else:
        raise ValueError("Unknown shell type %s" % shell)
    return (env_lines % (fsldir), match, replace % (fsldir))


def get_profile(shell):
    home = os.path.expanduser("~")

    dotprofile = os.path.join(home, '.profile')
    if shell == 'bash':
        profile = os.path.join(home, '.bash_profile')
        if not os.path.isfile(profile) and os.path.isfile(dotprofile):
            profile = dotprofile
    elif shell == 'zsh':
        profile = os.path.join(home, '.zprofile')
        # ZSH will never source .profile
    elif shell == 'sh':
        profile = dotprofile
    else:
        cshprofile = os.path.join(home, '.cshrc')
        if shell == 'csh':
            profile = cshprofile
        elif shell == 'tcsh':
            profile = os.path.join(home, '.tcshrc')
            if not os.path.isfile(profile) and os.path.isfile(cshprofile):
                profile = cshprofile
        else:
            raise ValueError("Unsupported shell")
    return profile


class FixFslDirError(Exception):
    pass


def fix_fsldir(shell, fsldir):
    (_, match, replace) = shell_config(shell, fsldir)
    profile = get_profile(shell)
    MsgUser.debug(
            "Editing %s, replacing line beginning:%s with %s." %
            (profile, match, replace))
    try:
        edit_file(profile, line_starts_replace, match, replace, False)
    except EditFileError as e:
        raise FixFslDirError(str(e))


class AddFslDirError(Exception):
    pass


def add_fsldir(shell, fsldir):
    (env_lines, _, _) = shell_config(shell, fsldir)
    profile = get_profile(shell)
    MsgUser.debug("Adding %s to %s" % (env_lines, profile))
    try:
        add_to_file(profile, env_lines, False)
    except AddToFileError as e:
        raise AddFslDirError(str(e))


class SetupEnvironmentError(Exception):
    pass


class SetupEnvironmentSkip(Exception):
    pass


def setup_system_environment(fsldir):
    """Add a system-wide profile setting up FSL for all users.
    Only supported on Redhat/Centos"""
    profile_d = '/etc/profile.d'
    profile_files = ['fsl.sh', 'fsl.csh']
    exceptions = []
    skips = []

    if os.getuid() != 0:
        sudo = True
    else:
        sudo = False

    if os.path.isdir(profile_d):
        for profile in profile_files:
            pf = profile.split('.')[1]
            (lines, match, replace) = shell_config(pf, fsldir)
            this_profile = os.path.join(profile_d, profile)
            if os.path.exists(this_profile):
                # Already has a profile file
                # Does it contain an exact match for current FSLDIR?
                match = file_contains_1stline(this_profile, replace)
                if match != '':
                    # If there is an fsl.(c)sh then just fix
                    # the entry for FSLDIR
                    MsgUser.debug(
                            "Fixing %s for FSLDIR location." % (this_profile))
                    try:
                        edit_file(
                                this_profile, line_starts_replace,
                                match, replace, sudo)
                    except EditFileError as e:
                        exceptions.append(str(e))
                else:
                    # No need to do anything
                    MsgUser.debug(
                            "%s already configured - skipping." %
                            (this_profile))
                    skips.append(profile)
            else:
                # Create the file
                try:
                    create_file(this_profile, lines, sudo)
                except CreateFileError as e:
                    exceptions.append(str(e))

    else:
        raise SetupEnvironmentError(
            "No system-wide configuration folder found - Skipped")
    if exceptions:
        raise SetupEnvironmentError(".".join(exceptions))
    if skips:
        raise SetupEnvironmentSkip(".".join(skips))


def setup_environment(fsldir=None):
    """Setup the user's environment so that their
    terminal finds the FSL tools etc."""
    # Check for presence of profile file:
    if fsldir is None:
        fsldir = get_fsldir()

    user_shell = which_shell()
    MsgUser.debug("User's shell is %s" % (user_shell))
    try:
        (profile_lines, _, _) = shell_config(user_shell, fsldir)
        profile = get_profile(user_shell)
    except ValueError as e:
        raise SetupEnvironmentError(str(e))

    cfile = False
    if not os.path.isfile(profile):
        MsgUser.debug("User is missing a shell setup file.")
        cfile = True

    if cfile:
        MsgUser.debug("Creating file %s" % (profile))
        try:
            create_file(profile, profile_lines, False)
        except CreateFileError as e:
            raise SetupEnvironmentError(
                    "Unable to create profile %s" % (profile))
    else:
        # Check if user already has FSLDIR set
        MsgUser.message("Setting up FSL software...")
        try:
            if file_contains(profile, "FSLDIR"):
                MsgUser.debug("Updating FSLDIR entry.")
                fix_fsldir(user_shell, fsldir)
            else:
                MsgUser.debug("Adding FSLDIR entry.")
                add_fsldir(user_shell, fsldir)
        except (AddFslDirError, FixFslDirError) as e:
            raise SetupEnvironmentError(
                    "Unable to update your profile %s"
                    " with FSL settings" % (profile))


class PostInstallError(Exception):
    pass


class InstallArchiveError(Exception):
    pass


class UnknownArchiveType(Exception):
    pass


def archive_type(archive):
    """Determine file type based on extension and check
    that file looks like this file type"""
    archive_types = {
        'gzip': ('tar', '-z'),
        'bzip2': ('tar', '-j'),
        'zip': ('zip', ''), }

    try:
        file_type = run_cmd("file %s" % (archive))
    except RunCommandError as e:
        raise UnknownArchiveType(str(e))
    file_type = file_type.lower()
    for f_type in ('gzip', 'bzip2', 'zip', ):
        if f_type in file_type:
            return archive_types[f_type]
    raise UnknownArchiveType(archive)


def post_install(
        fsldir, settings, script="post_install.sh", quiet=False,
        app_links=False):
    MsgUser.message("Performing post install tasks")
    if is_writeable(fsldir):
        as_root = False
    elif is_writeable_as_root(fsldir):
        as_root = True
    else:
        raise PostInstallError(
                "Unable to write to target folder (%s)" % fsldir)
    install_installer(fsldir)
    script_path = os.path.join(fsldir, Settings.post_inst_dir, script)

    if os.path.exists(script_path):
        MsgUser.debug("Found post-install script %s" % script_path)
        if not os.access(script_path, os.X_OK):
            raise PostInstallError(
                "Unable to run post install script %s" % script_path
            )
        script_opts = '-f "%s"' % fsldir
        if quiet:
            script_opts += " -q"

        command_line = " ".join((script_path, script_opts))
        try:
            run_cmd_displayoutput(command_line, as_root=as_root)
        except RunCommandError as e:
            raise PostInstallError(
                "Error running post installation script (error %s)"
                " - check the install log" % (str(e))
            )
        # Work around for mistake in 5.0.10 post setup script
        mal = os.path.join(
                    fsldir, Settings.post_inst_dir,
                    'make_applications_links.sh')
        if (os.path.exists(mal) and
                not file_contains(script_path, "make_applications_links.sh")):
            MsgUser.debug(
                "Work around necessary for missing app link creation")
        else:
            app_links = False
    if app_links:
        try:
            make_applications_links(fsldir, settings.applications)
        except MakeApplicationLinksError as e:
            for message in e.app_messages.values():
                MsgUser.warning(message)
        else:
            MsgUser.ok("/Applications links created/updated")

    MsgUser.ok("Post installation setup complete")


def install_archive(archive, fsldir=None):
    def clean_up_temp():
        try:
            safe_delete(tempfolder,  as_root)
        except SafeDeleteError as sd_e:
            MsgUser.debug(
                    "Unable to clean up temporary folder! "
                    "%s" % (str(sd_e)))
    if not os.path.isfile(archive):
        raise InstallError("%s isn't a file" % (archive))
    if not fsldir:
        try:
            fsldir = get_fsldir(specified_dir=fsldir, install=True)
        except GetFslDirError as e:
            raise InstallError(str(e))

    MsgUser.debug("Requested install of %s as %s" % (archive, fsldir))
    if os.path.exists(fsldir):
        # move old one out of way
        MsgUser.debug("FSL version already installed")
        keep_old = Settings.inst_qus.ask_question('del_old')
    else:
        keep_old = False

    install_d = os.path.dirname(fsldir)
    MsgUser.debug("Checking %s is writeable." % (install_d))
    if is_writeable(install_d):
        as_root = False
    elif is_writeable_as_root(install_d):
        as_root = True
    else:
        raise InstallArchiveError(
                "Unable to write to target folder (%s), "
                "even as a super user." % (install_d))
    MsgUser.debug("Does %s require root for deletion? %s" % (
            install_d, as_root))
    try:
        unarchive, ua_option = archive_type(archive)
    except UnknownArchiveType as e:
        raise InstallArchiveError(str(e))
    # Generate a temporary name - eg fsl-<mypid>-date
    tempname = '-'.join(('fsl', str(os.getpid()), str(time.time())))
    tempfolder = os.path.join(install_d, tempname)
    try:
        run_cmd_dropstdout("mkdir %s" % (tempfolder), as_root=as_root)
    except RunCommandError as e:
        raise InstallArchiveError(
                "Unable to create folder to install into.")
    MsgUser.debug(
            "Unpacking %s into folder %s." % (archive, tempfolder))
    try:
        if unarchive == 'tar':
            unpack_cmd = 'tar -C %s -x %s -o -f %s' % (
                tempfolder, ua_option, archive)
        elif unarchive == 'zip':
            MsgUser.debug(
                "Calling unzip %s %s" % (ua_option, archive)
            )
            unpack_cmd = 'unzip %s %s' % (ua_option, archive)

        try:
            run_cmd_dropstdout(unpack_cmd, as_root=as_root)
        except RunCommandError as e:
            raise InstallArchiveError("Unable to unpack FSL.")

        new_fsl = os.path.join(tempfolder, 'fsl')
        if os.path.exists(fsldir):
            # move old one out of way
            try:
                old_version = get_installed_version(fsldir)
            except (NotAFslVersion, GetInstalledVersionError) as e:
                if keep_old:
                    old_version = '0.0.0'
                    MsgUser.warning(
                            "The contents of %s doesn't look like an "
                            "FSL installation! - "
                            "moving to fsl-0.0.0" % (fsldir))
            old_fsl = '-'.join((fsldir, str(old_version)))
            if os.path.exists(old_fsl):
                MsgUser.debug(
                        "Looks like there is another copy of the "
                        "old version of FSL - deleting...")
                try:
                    safe_delete(old_fsl, as_root)
                except SafeDeleteError as e:
                    raise InstallError(
                            ";".join((
                                    "Install location already has a "
                                    "%s - I've tried to delete it but"
                                    " failed" % (old_fsl), str(e))))

            if keep_old:
                try:
                    MsgUser.debug(
                        "Moving %s to %s" % (fsldir, old_fsl))
                    move(fsldir, old_fsl, as_root)
                    MsgUser.message(
                        '''You can find your archived version of FSL in %s.
If you wish to restore it, remove %s and rename %s to %s''' % (
                            old_fsl, fsldir, old_fsl, fsldir))

                except MoveError as mv_e:
                    # failed to move the old version
                    MsgUser.debug(
                        "Failed to move old version "
                        "- %s" % (str(mv_e)))
                    raise InstallError(
                        "Failed to backup old version (%s)" % (str(mv_e)))
            else:
                MsgUser.debug("Removing existing FSL install")
                try:
                    safe_delete(fsldir, as_root)
                    MsgUser.debug("Deleted %s." % (fsldir))
                except SafeDeleteError as e:
                    raise InstallError(
                            "Failed to delete %s - %s." % (fsldir, str(e)))
        else:
            old_fsl = ''
        try:
            MsgUser.debug("Moving %s to %s" % (new_fsl, fsldir))
            move(new_fsl, fsldir, as_root)
        except MoveError as e:
            # Unable to move new install into place
            MsgUser.debug(
                    "Move failed - %s." % (str(e)))
            raise InstallError(
                    'Failed to move new version into place.')

    except InstallError as e:
        clean_up_temp()
        raise InstallArchiveError(str(e))

    clean_up_temp()
    MsgUser.debug("Install complete")
    MsgUser.ok("FSL software installed.")
    return fsldir


class MakeApplicationLinksError(Exception):
    def __init__(self, *args):
        super(MakeApplicationLinksError, self).__init__(*args)
        try:
            self.app_messages = args[0]
        except IndexError:
            self.app_messages = []


def make_applications_links(fsldir, apps):
    """Create symlinks in /Applications"""
    MsgUser.message("Creating Application links...")
    results = {}
    for app in apps:
        app_location = os.path.join('/Applications', os.path.basename(app))
        app_target = os.path.join(fsldir, app)
        create_link = True
        MsgUser.debug("Looking for existing link %s" % (app_location))
        if os.path.lexists(app_location):
            MsgUser.debug(
                    "Is a link: %s; realpath: %s" % (
                            os.path.islink(app_location),
                            os.path.realpath(app_location)))
            if os.path.islink(app_location):
                MsgUser.debug("A link already exists.")
                if os.path.realpath(app_location) != app_target:
                    MsgUser.debug(
                        "Deleting old (incorrect) link %s" % (app_location))
                    try:
                        run_cmd_dropstdout("rm " + app_location, as_root=True)
                    except RunCommandError as e:
                        MsgUser.debug(
                                "Unable to remove broken"
                                " link to %s (%s)." % (app_target, str(e)))
                        results[app] = 'Unable to remove broken link to %s' % (
                            app_target)
                        create_link = False
                else:
                    MsgUser.debug("Link is correct, skipping.")
                    create_link = False
            else:
                MsgUser.debug(
                        "%s doesn't look like a symlink, "
                        "so let's not delete it." % (app_location))
                results[app] = (
                    "%s is not a link so hasn't been updated to point at the "
                    "new FSL install.") % (app_location)
                create_link = False
        if create_link:
            MsgUser.debug('Create a link for %s' % (app))
            if os.path.exists(app_target):
                try:
                    run_cmd_dropstdout(
                            "ln -s %s %s" % (app_target, app_location),
                            as_root=True)
                except RunCommandError as e:
                    MsgUser.debug(
                            "Unable to create link to %s (%s)." % (
                                    app_target, str(e)))
                    results[app] = (
                        'Unable to create link to %s.') % (app_target)
            else:
                MsgUser.debug(
                    'Unable to find application'
                    ' %s to link to.') % (app_target)
    if results:
        raise MakeApplicationLinksError(results)


def do_install(options, settings):
    MsgUser.message(
        ShellColours.bold + settings.title + ShellColours.default)

    if options.test_installer:
        settings.main_mirror = options.test_installer

    this_computer = Host
    if not this_computer.supported:
        MsgUser.debug("Unsupported host %s %s %s" % (
                        this_computer.o_s,
                        this_computer.arch,
                        this_computer.os_type))
        raise InstallError(
            "Unsupported host - you could try building from source")

    if this_computer.o_s == "linux":
        system_environment = True
        with_matlab = False
        application_links = False
        x11 = False
    else:
        MsgUser.debug("Unrecognised OS %s" % (this_computer.o_s))
        raise InstallError("Unrecognised OS")

    my_uid = os.getuid()

    def configure_environment(fsldir, env_all=False, skip=False, matlab=False):
        if skip:
            return
        if env_all:
            if system_environment:
                # Setup the system-wise environment
                try:
                    setup_system_environment(fsldir)
                except SetupEnvironmentError as e:
                    MsgUser.debug(str(e))
                    MsgUser.failed(
                        "Failed to configure system-wide profiles "
                        "with FSL settings: %s" % (str(e)))
                except SetupEnvironmentSkip as e:
                    MsgUser.skipped(
                        "Some shells already configured: %s" % (str(e)))
                else:
                    MsgUser.debug("System-wide profiles setup.")
                    MsgUser.ok("System-wide FSL configuration complete.")
            else:
                MsgUser.skipped(
                    "System-wide profiles not supported on this OS")
        elif my_uid != 0:
            # Setup the environment for the current user
            try:
                setup_environment(fsldir, with_matlab=matlab)
            except SetupEnvironmentError as e:
                MsgUser.debug(str(e))
                MsgUser.failed(str(e))
            else:
                MsgUser.ok(
                    "User profile updated with FSL settings, you will need "
                    "to log out and back in to use the FSL tools.")

    if my_uid != 0:
        if options.quiet:
            settings.inst_qus.defaults = True
            print('''
We may need administrator rights, but you have specified fully automated
mode - you may still be asked for an admin password if required.''')
            print('''
To install fully automatedly, either ensure this is running as the root
user (use sudo) or that you can write to the folder you wish to install
FSL in.''')
        elif (not options.download and
                not options.list_versions and
                not options.get_source and
                not options.get_feeds):
            MsgUser.warning(
                '''Some operations of the installer require administative rights,
    for example installing into the default folder of /usr/local.
    If your account is an 'Administrator' (you have 'sudo' rights)
    then you will be prompted for your administrator password
    when necessary.''')
    if not options.d_dir and options.quiet:
        raise InstallError(
            "Quiet mode requires you to specify the install location"
            " (e.g. /usr/local)")
    if not options.quiet and not options.list_versions:
        MsgUser.message(
            "When asked a question, the default answer is given in square "
            "brackets.\nHit the Enter key to accept this default answer.")
    if options.env_only and my_uid != 0:
        configure_environment(
            get_fsldir(specified_dir=options.d_dir),
            options.env_all)
        return
    if options.archive:
        if not options.skipchecksum:
            if not options.checksum:
                raise InstallError(
                    "No checksum provided and checking not disabled")
            else:
                checksummer = globals()[options.checksum_type + 'File']
                if options.checksum != checksummer(options.archive):
                    raise InstallError("FSL archive doesn't match checksum")
                else:
                    MsgUser.ok("FSL Package looks good")
        arc_version = archive_version(options.archive)
        MsgUser.message(
            "Installing FSL software version %s..." % arc_version)

        fsldir = install_archive(
            archive=options.archive, fsldir=options.d_dir)
        try:
            post_install(fsldir=fsldir, settings=settings, quiet=options.quiet)
        except PostInstallError as e:
            raise InstallError(str(e))
        configure_environment(
            fsldir=fsldir, env_all=options.env_all,
            skip=options.skip_env, matlab=with_matlab)
        return

    # All the following options require the Internet...
    if options.download:
        MsgUser.debug("Attempting to download latest release")
        try:
            download_release(request_version=options.requestversion,
                             skip_verify=options.skipchecksum)
        except DownloadFileError as e:
            raise("Unable to download release %s" % (str(e)))
        return

    if options.get_source:
        MsgUser.debug("Attempting to download source")
        try:
            download_release(
                request_version=options.requestversion,
                skip_verify=options.skipchecksum,
                source_code=True)
        except DownloadFileError as e:
            raise("Unable to download source code %s" % (str(e)))
        return

    if options.get_feeds:
        MsgUser.debug("Attempting to download FEEDS")
        try:
            download_release(
                request_version=options.requestversion,
                skip_verify=options.skipchecksum,
                feeds=True)
        except DownloadFileError as e:
            raise("Unable to download FEEDS %s" % (str(e)))
        return

    try:
        fsldir = get_fsldir(specified_dir=options.d_dir, install=True)
        reinstall = True
        if os.path.exists(fsldir):
            inst_version = get_installed_version(fsldir)
        if reinstall:
            (fname, version, details) = download_release(
                to_temp=True,
                request_version=options.requestversion,
                skip_verify=options.skipchecksum)
            if not details['supported']:
                MsgUser.debug(
                    "This OS is not officially supported -"
                    " you may experience issues"
                )
            MsgUser.debug(
                "Installing %s from %s (details: %s)" % (
                    fname, version, details))
            MsgUser.message(
                "Installing FSL software version %s..." % version)
            install_archive(
                archive=fname, fsldir=fsldir)
            try:
                safe_delete(fname)
            except SafeDeleteError as e:
                MsgUser.debug(
                    "Unable to delete downloaded package %s ; %s" % (
                        fname, str(e)))
            if details['notes']:
                MsgUser.message(details['notes'])
            try:
                post_install(
                    fsldir=fsldir, settings=settings,
                    quiet=options.quiet, x11=x11,
                    app_links=application_links)
            except PostInstallError as e:
                raise InstallError(str(e))

    except DownloadError as e:
        MsgUser.debug("Unable to download FSL %s" % (str(e)))
        raise InstallError("Unable to download FSL")
    except InstallArchiveError as e:
        MsgUser.debug("Unable to unpack FSL ; %s" % (str(e)))
        raise InstallError("Unable to unpack FSL - %s" % (str(e)))

    configure_environment(
        fsldir=fsldir, env_all=options.env_all,
        skip=options.skip_env, matlab=with_matlab)

    if details['notes']:
        MsgUser.message(details['notes'])


def parse_options(args):
    usage = "usage: %prog [options]"
    ver = "%%prog 3.0.18"
    parser = OptionParser(usage=usage, version=ver)
    parser.add_option("-d", "--dest", dest="d_dir",
                      help="Install into folder given by DESTDIR - "
                      "e.g. /usr/local/fsl",
                      metavar="DESTDIR", action="store",
                      type="string")
    parser.add_option("-e", dest="env_only",
                      help="Only setup/update your environment",
                      action="store_true")
    parser.add_option("-E", dest="env_all",
                      help="Setup/update the environment for ALL users",
                      action="store_true")
    parser.add_option("-v", help="Print version number and exit",
                      action="version")
    parser.add_option("-c", "--checkupdate", dest='update',
                      help="Check for FSL updates -"
                      " needs an internet connection",
                      action="store_true")
    parser.add_option("-o", "--downloadonly", dest="download",
                      help=SUPPRESS_HELP,
                      action="store_true")

    advanced_group = OptionGroup(
            parser, "Advanced Install Options",
            "These are advanced install options")
    advanced_group.add_option(
            "-l", "--listversions", dest="list_versions",
            help="List available versions of FSL",
            action="store_true")
    advanced_group.add_option(
            "-V", "--fslversion", dest="requestversion",
            help="Download the specific version FSLVERSION of FSL",
            metavar="FSLVERSION", action="store",
            type="string")
    advanced_group.add_option(
            "-s", "--source", dest="get_source",
            help="Download source code for FSL",
            action="store_true")
    advanced_group.add_option(
            "-F", "--feeds", dest="get_feeds",
            help="Download FEEDS",
            action="store_true")
    advanced_group.add_option(
            "-q", "--quiet", dest='quiet',
            help="Silence all messages - useful if scripting install",
            action="store_true")
    advanced_group.add_option(
            "-p", dest="skip_env",
            help="Don't setup the environment",
            action="store_true")
    parser.add_option_group(advanced_group)

    debug_group = OptionGroup(
        parser, "Debugging Options",
        "These are for use if you have a problem running this installer.")
    debug_group.add_option(
        "-f", "--file", dest="archive",
        help="Install a pre-downloaded copy of the FSL archive",
        metavar="ARCHIVEFILE", action="store",
        type="string")
    debug_group.add_option(
        "-C", "--checksum", dest="checksum",
        help="Supply the expected checksum for the pre-downloaded FSL archive",
        metavar="CHECKSUM", action="store",
        type="string")
    debug_group.add_option(
        "-T", "--checksum-type", dest="checksum_type",
        default="sha256",
        help="Specify the type of checksum",
        action="store",
        type="string")
    debug_group.add_option(
        "-M", "--nochecksum", dest="skipchecksum",
        help="Don't check the pre-downloaded FSL archive",
        action="store_true")
    debug_group.add_option(
        "-D", dest="verbose",
        help="Switch on debug messages",
        action="store_true")
    debug_group.add_option(
        "-G", dest="test_installer",
        help=SUPPRESS_HELP,
        action="store",
        type="string")
    debug_group.add_option(
        "-w", dest="test_csv",
        help=SUPPRESS_HELP,
        action="store_true"
    )
    parser.add_option_group(debug_group)
    return parser.parse_args(args)


if __name__ == '__main__':
    (options, args) = parse_options(sys.argv[1:])
    if options.verbose:
        MsgUser.debug_on()
        print(options)
    if options.quiet:
        MsgUser.quiet_on()
    installer_settings = Settings()
    try:
        do_install(options, installer_settings)
    except (InstallError, GetFslDirError, GetInstalledVersionError) as e:
        MsgUser.failed(str(e))
        sys.exit(1)
    except KeyboardInterrupt as e:
        MsgUser.message('')
        MsgUser.failed("Install aborted.")
        sys.exit(1)
