"""OpenBB 平台版本脚本

本模块提供 OpenBB 平台的版本信息获取功能。

版本格式
--------

- 正式版本: "x.y.z"
- 开发版本: "x.y.zdev" (从 git 仓库运行时)
- 夜间版本: "x.y.z" (openbb-nightly 包)
- 仅核心: "x.y.zcore" (仅安装 openbb-core 时)
"""

from importlib.metadata import (
    PackageNotFoundError,
    version as pkg_version,
)
from pathlib import Path

# 主包名称
PACKAGE = "openbb"


def get_package_version(package: str):
    """获取包版本号

    从已安装的 pip 包中获取版本信息。
    如果在 git 仓库中运行，会在版本后添加 "dev" 后缀。

    Parameters
    ----------
    package : str
        包名称

    Returns
    -------
    str
        版本字符串
    """
    is_nightly = False
    try:
        version = pkg_version(package)
    except PackageNotFoundError:
        package += "-nightly"
        is_nightly = True
        try:
            version = pkg_version(package)
        except PackageNotFoundError:
            package = "openbb-core"
            version = pkg_version(package)
            version += "core"

    if is_git_repo(Path(__file__).parent.resolve()) and not is_nightly:
        version += "dev"

    return version


def is_git_repo(path: Path):
    """检查指定目录是否为 git 仓库

    Parameters
    ----------
    path : Path
        要检查的目录路径

    Returns
    -------
    bool
        如果是 git 仓库返回 True，否则返回 False
    """
    # pylint: disable=import-outside-toplevel
    import shutil
    import subprocess

    git_executable = shutil.which("git")
    if not git_executable:
        return False
    try:
        subprocess.run(  # noqa: S603
            [git_executable, "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_major_minor(version: str) -> tuple[int, int]:
    """从版本字符串中提取主版本号和次版本号

    Parameters
    ----------
    version : str
        版本字符串，如 "1.2.3"

    Returns
    -------
    tuple[int, int]
        (主版本号, 次版本号) 元组
    """
    parts = version.split(".")
    return (int(parts[0]), int(parts[1]))


try:
    VERSION = get_package_version(PACKAGE)
except PackageNotFoundError:
    VERSION = "unknown"

try:
    CORE_VERSION = get_package_version("openbb-core")
except PackageNotFoundError:
    CORE_VERSION = "unknown"
