# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

from pathlib import Path
from typing import Union
from rich import print as richprint


def summary_msg(
    nfiles, tarname: Union[Path, None] = None, wdir: Union[Path, None] = None
):
    """Return summary msg to print at end of run"""

    def _num_tag(n: int):
        return f"[bold]{n} file" + ("s" if n > 1 else "") + "[/]"

    if tarname:
        try:
            tarname_rel = tarname.relative_to(wdir if wdir else tarname.root)
        except ValueError:
            tarname_rel = tarname
        finally:
            richprint(
                f"[cyan]Summary: :package: [bold]{tarname_rel}[/] generated with"
                f" {_num_tag(nfiles)}.[/]"
            )
    else:
        richprint(
            f"[cyan]Summary: :clipboard: {_num_tag(nfiles)} to include.[/]"
        )
