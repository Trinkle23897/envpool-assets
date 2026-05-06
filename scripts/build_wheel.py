#!/usr/bin/env python3

"""Build an envpool-assets wheel from a prepared asset root."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

ASSET_PATHS = (
    "atari/roms",
    "gfootball/assets",
    "mujoco/assets_dmc",
    "mujoco/assets_gym",
    "mujoco/metaworld/assets",
    "mujoco/myosuite/assets",
    "mujoco/robotics/assets",
    "procgen/assets",
    "vizdoom/bin/freedoom2.wad",
    "vizdoom/maps",
)

FORBIDDEN_PATHS = (
    "vizdoom/bin/vizdoom",
    "vizdoom/bin/vizdoom.pk3",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asset-root",
        type=Path,
        required=True,
        help="Directory containing the EnvPool asset subtrees.",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="envpool-assets package version.",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="Directory where the built wheel should be written.",
    )
    return parser.parse_args()


def _asset_root_complete(asset_root: Path) -> bool:
    return all((asset_root / asset_path).exists() for asset_path in ASSET_PATHS)


def _validate_asset_root(asset_root: Path) -> Path:
    asset_root = asset_root.resolve()
    if not _asset_root_complete(asset_root):
        missing = [
            asset_path
            for asset_path in ASSET_PATHS
            if not (asset_root / asset_path).exists()
        ]
        raise FileNotFoundError(
            f"{asset_root} is missing required asset paths: {missing}"
        )
    forbidden = [
        asset_path
        for asset_path in FORBIDDEN_PATHS
        if (asset_root / asset_path).exists()
    ]
    if forbidden:
        raise RuntimeError(
            f"Asset wheel must not contain platform-specific EnvPool files: {forbidden}"
        )
    return asset_root


def _copy_tree(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=False)
    else:
        shutil.copy2(src, dst)


def _copy_assets(asset_root: Path, package_dir: Path) -> None:
    for asset_path in ASSET_PATHS:
        _copy_tree(asset_root / asset_path, package_dir / asset_path)


def _write_package_init(package_dir: Path, version: str) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "__init__.py").write_text(
        "\n".join(
            [
                '"""Runtime assets for EnvPool."""',
                "",
                "from pathlib import Path",
                "",
                f'__version__ = "{version}"',
                "",
                "",
                "def asset_path() -> Path:",
                '    """Return the root directory containing EnvPool asset subtrees."""',
                "    return Path(__file__).resolve().parent",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_setup_py(build_root: Path, repo_root: Path, version: str) -> None:
    readme = repo_root / "README.md"
    license_file = repo_root / "LICENSE"
    if readme.is_file():
        shutil.copy2(readme, build_root / "README.md")
    if license_file.is_file():
        shutil.copy2(license_file, build_root / "LICENSE")

    (build_root / "setup.py").write_text(
        "\n".join(
            [
                "from setuptools import find_namespace_packages, setup",
                "",
                "setup(",
                '    name="envpool-assets",',
                f'    version="{version}",',
                '    author="EnvPool Contributors",',
                '    author_email="sail@sea.com",',
                '    description="Runtime data assets for EnvPool.",',
                '    long_description=open("README.md", encoding="utf-8").read(),',
                '    long_description_content_type="text/markdown",',
                '    url="https://github.com/Trinkle23897/envpool-assets",',
                '    packages=find_namespace_packages(include=["envpool_assets*"]),',
                '    package_data={"": ["*"]},',
                "    include_package_data=True,",
                '    python_requires=">=3.11",',
                '    license="Apache-2.0",',
                '    classifiers=["Programming Language :: Python :: 3"],',
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _build_wheel(build_root: Path, dist_dir: Path) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "setup.py",
        "bdist_wheel",
        "--quiet",
        "--dist-dir",
        str(dist_dir.resolve()),
    ]
    result = subprocess.run(
        command,
        cwd=build_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, command)


def _built_wheel(dist_dir: Path, version: str) -> Path:
    matches = sorted(dist_dir.glob(f"envpool_assets-{version}-*.whl"))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one envpool-assets wheel in {dist_dir}, found {matches}"
        )
    return matches[0]


def _check_wheel_contents(wheel_path: Path) -> None:
    with ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
    for asset_path in ASSET_PATHS:
        package_path = f"envpool_assets/{asset_path}"
        if not any(
            name == package_path or name.startswith(f"{package_path}/")
            for name in names
        ):
            raise RuntimeError(f"Built wheel is missing {package_path}")
    for asset_path in FORBIDDEN_PATHS:
        package_path = f"envpool_assets/{asset_path}"
        if package_path in names:
            raise RuntimeError(
                f"Built wheel contains forbidden platform-specific file {package_path}"
            )


def main() -> None:
    """Build the envpool-assets wheel."""
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    asset_root = _validate_asset_root(args.asset_root)
    version = args.version

    with tempfile.TemporaryDirectory(prefix="envpool-assets-wheel-") as tmpdir:
        build_root = Path(tmpdir)
        package_dir = build_root / "envpool_assets"
        _write_package_init(package_dir, version)
        _copy_assets(asset_root, package_dir)
        _write_setup_py(build_root, repo_root, version)
        _build_wheel(build_root, args.dist_dir)

    wheel_path = _built_wheel(args.dist_dir, version)
    _check_wheel_contents(wheel_path)
    print(wheel_path)


if __name__ == "__main__":
    main()
