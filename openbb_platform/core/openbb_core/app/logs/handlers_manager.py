"""日志处理器管理模块

本模块提供日志处理器的管理功能。
"""

import logging
import sys

from openbb_core.app.logs.formatters.formatter_with_exceptions import (
    FormatterWithExceptions,
)
from openbb_core.app.logs.handlers.path_tracking_file_handler import (
    PathTrackingFileHandler,
)
from openbb_core.app.logs.models.logging_settings import LoggingSettings


class HandlersManager:
    """日志处理器管理器

    管理日志处理器的创建、配置和更新。

    Attributes
    ----------
    _logger : logging.Logger
        日志记录器
    _handlers : list[str]
        处理器类型列表
    _settings : LoggingSettings
        日志设置
    """

    def __init__(self, logger: logging.Logger, settings: LoggingSettings):
        """初始化处理器管理器"""
        self._logger = logger
        self._handlers = settings.handler_list
        self._settings = settings

    def setup(self):
        """设置日志处理器和配置"""
        # Disable propagation to root logger to avoid duplicate logs
        self._logger.propagate = False
        self._logger.setLevel(self._settings.verbosity)

        for handler_type in self._handlers:
            if handler_type == "stdout":
                self._add_stdout_handler()
            elif handler_type == "stderr":
                self._add_stderr_handler()
            elif handler_type == "noop":
                self._add_noop_handler()
            elif handler_type == "file" and not self._settings.logging_suppress:
                self._add_file_handler()
            else:
                self._logger.debug("Unknown log handler.")

    def _add_stdout_handler(self):
        """添加标准输出处理器"""
        handler = logging.StreamHandler(sys.stdout)
        formatter = FormatterWithExceptions(settings=self._settings)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _add_stderr_handler(self):
        """添加标准错误处理器"""
        handler = logging.StreamHandler(sys.stderr)
        formatter = FormatterWithExceptions(settings=self._settings)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _add_noop_handler(self):
        """添加空处理器"""
        handler = logging.NullHandler()
        formatter = FormatterWithExceptions(settings=self._settings)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _add_file_handler(self):
        """添加文件处理器"""
        handler = PathTrackingFileHandler(settings=self._settings)
        formatter = FormatterWithExceptions(settings=self._settings)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def update_handlers(self, settings: LoggingSettings):
        """使用新设置更新处理器"""
        logger = self._logger
        for hdlr in logger.handlers:
            if (
                isinstance(hdlr, PathTrackingFileHandler)
                and not settings.logging_suppress
            ):
                hdlr.settings = settings
                hdlr.formatter.settings = settings  # type: ignore
