"""OpenBB Platform CLI 入口模块

命令行界面的主入口点，负责启动和配置 CLI。
"""

import logging
import sys

from openbb_cli.utils.utils import change_logging_sub_app, reset_logging_sub_app


def main():
    """OpenBB Platform CLI 主入口函数。"""
    print("Loading...\n")  # noqa: T201

    # pylint: disable=import-outside-toplevel
    from openbb_cli.config.setup import bootstrap
    from openbb_cli.controllers.cli_controller import launch

    bootstrap()

    dev = "--dev" in sys.argv[1:]
    debug = "--debug" in sys.argv[1:]

    launch(dev, debug)


if __name__ == "__main__":
    initial_logging_sub_app = change_logging_sub_app()
    try:
        main()
    except Exception:
        logging.exception("An unexpected error occurred")
    finally:
        reset_logging_sub_app(initial_logging_sub_app)
