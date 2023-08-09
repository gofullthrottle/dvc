import logging
from argparse import SUPPRESS, ArgumentParser
from typing import Tuple

import pytest
import shtab

from dvc.cli import main
from dvc.cli.parser import get_main_parser


def command_tuples():
    root: Tuple[str, ...] = ()
    commands = [root]

    def recurse_parser(parser: ArgumentParser, parents: Tuple[str, ...] = root) -> None:
        for positional in parser._get_positional_actions():
            if positional.help != SUPPRESS and isinstance(positional.choices, dict):
                public_cmds = shtab.get_public_subcommands(positional)
                for subcmd, subparser in positional.choices.items():
                    cmd = (*parents, subcmd)
                    if subcmd in public_cmds:
                        commands.append(cmd)
                    recurse_parser(subparser, cmd)

    main_parser = get_main_parser()
    recurse_parser(main_parser)
    return sorted(commands)


def pytest_generate_tests(metafunc):
    def ids(values):
        if values:
            return "-".join(values)
        return "dvc"

    metafunc.parametrize("command_tuples", command_tuples(), ids=ids)


def test_help(caplog, capsys, command_tuples):
    with caplog.at_level(logging.INFO), pytest.raises(SystemExit) as e:
        main([*command_tuples, "--help"])
    assert e.value.code == 0
    assert not caplog.text

    out, err = capsys.readouterr()
    assert not err
    assert out