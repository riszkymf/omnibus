"""
Usage:
  omnibus <command> [<args>...]

Run 'omnibus COMMAND --help' for more information on a command.
"""

from inspect import getmembers, isclass
from docopt import docopt, DocoptExit
from omnibus import __version__ as VERSION


def main():
    """Main CLI entrypoint."""
    import omnibus.clis
    options = docopt(__doc__, version=VERSION, options_first=True)
    command_name = ""
    args = ""
    command_class =""

    command_name = options.pop('<command>')
    args = options.pop('<args>')

    if args is None:
        args = {}

    try:
        module = getattr(omnibus.clis, command_name)
    
        omnibus.clis = getmembers(module, isclass)
        command_class = [command[1] for command in omnibus.clis
                   if command[0] != 'Base'][0]
    except AttributeError as e:
        print(e)
        raise DocoptExit()

    command = command_class(options, args)
    command.execute()


if __name__ == '__main__':
    main()
