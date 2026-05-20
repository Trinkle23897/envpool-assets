#!/usr/bin/env python3

"""Build an EnvPool asset wheel from a prepared asset root."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

PackageConfig = dict[str, object]


def _package_config(
    package: str,
    asset_paths: tuple[str, ...],
    forbidden_paths: tuple[str, ...] = (),
    distribution_name: str | None = None,
    module_name: str | None = None,
) -> PackageConfig:
    module_suffix = package.replace("-", "_")
    return {
        "distribution_name": distribution_name or f"envpool-assets-{package}",
        "module_name": module_name or f"envpool_assets_{module_suffix}",
        "asset_paths": asset_paths,
        "forbidden_paths": forbidden_paths,
    }


PACKAGE_CONFIGS: dict[str, PackageConfig] = {
    "base": _package_config(
        "base",
        (
            "atari/roms",
            "gfootball/assets",
            "mujoco/assets_dmc",
            "mujoco/assets_gym",
            "mujoco/metaworld/assets",
            "mujoco/robotics/assets",
            "procgen/assets",
            "vizdoom/bin/freedoom2.wad",
            "vizdoom/maps",
        ),
        ("vizdoom/bin/vizdoom", "vizdoom/bin/vizdoom.pk3"),
        distribution_name="envpool-assets",
        module_name="envpool_assets",
    ),
    "mujoco-large": _package_config(
        "mujoco-large",
        (
            "mujoco/myosuite/assets",
            "mujoco/playground/assets/mujoco_playground/_src/locomotion/go1",
            "mujoco/playground/assets/mujoco_playground/_src/locomotion/spot",
            "mujoco/playground/assets/mujoco_playground/_src/"
            "manipulation/aero_hand",
            "mujoco/playground/assets/mujoco_playground/_src/"
            "manipulation/aloha",
            "mujoco/playground/assets/mujoco_playground/_src/"
            "manipulation/franka_emika_panda",
            "mujoco/playground/assets/mujoco_playground/_src/"
            "manipulation/franka_emika_panda_robotiq",
            "mujoco/playground/assets/mujoco_playground/_src/"
            "manipulation/leap_hand",
            "mujoco/playground/assets/mujoco_menagerie/google_barkour_vb",
            "mujoco/playground/assets/mujoco_menagerie/unitree_go1",
            "mujoco/playground/assets/mujoco_menagerie/boston_dynamics_spot",
            "mujoco/playground/assets/mujoco_menagerie/"
            "tetheria_aero_hand_open",
            "mujoco/playground/assets/mujoco_menagerie/aloha",
            "mujoco/playground/assets/mujoco_menagerie/franka_emika_panda",
            "mujoco/playground/assets/mujoco_menagerie/robotiq_2f85_v4",
            "mujoco/playground/assets/mujoco_menagerie/leap_hand",
        ),
    ),
    "mujoco-playground-humanoid": _package_config(
        "mujoco-playground-humanoid",
        (
            "mujoco/playground/assets/mujoco_playground/_src/"
            "locomotion/apollo",
            "mujoco/playground/assets/mujoco_playground/_src/"
            "locomotion/berkeley_humanoid",
            "mujoco/playground/assets/mujoco_playground/_src/locomotion/g1",
            "mujoco/playground/assets/mujoco_playground/_src/locomotion/h1",
            "mujoco/playground/assets/mujoco_playground/_src/locomotion/op3",
            "mujoco/playground/assets/mujoco_playground/_src/locomotion/t1",
            "mujoco/playground/assets/mujoco_menagerie/apptronik_apollo",
            "mujoco/playground/assets/mujoco_menagerie/"
            "berkeley_humanoid",
            "mujoco/playground/assets/mujoco_menagerie/unitree_g1",
            "mujoco/playground/assets/mujoco_menagerie/unitree_h1",
            "mujoco/playground/assets/mujoco_menagerie/robotis_op3",
            "mujoco/playground/assets/mujoco_menagerie/booster_t1",
        ),
    ),
}


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
        help="Asset package version.",
    )
    parser.add_argument(
        "--package",
        choices=sorted(PACKAGE_CONFIGS),
        required=True,
        help="Asset package profile to build.",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="Directory where the built wheel should be written.",
    )
    return parser.parse_args()


def _asset_root_complete(
    asset_root: Path, asset_paths: tuple[str, ...]
) -> bool:
    return all((asset_root / asset_path).exists() for asset_path in asset_paths)


def _validate_asset_root(
    asset_root: Path,
    asset_paths: tuple[str, ...],
    forbidden_paths: tuple[str, ...],
) -> Path:
    asset_root = asset_root.resolve()
    if not _asset_root_complete(asset_root, asset_paths):
        missing = [
            asset_path
            for asset_path in asset_paths
            if not (asset_root / asset_path).exists()
        ]
        raise FileNotFoundError(
            f"{asset_root} is missing required asset paths: {missing}"
        )
    forbidden = [
        asset_path
        for asset_path in forbidden_paths
        if (asset_root / asset_path).exists()
    ]
    if forbidden:
        raise RuntimeError(
            "Asset wheel must not contain platform-specific EnvPool files: "
            f"{forbidden}"
        )
    return asset_root


def _copy_tree(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=False)
    else:
        shutil.copy2(src, dst)


def _copy_assets(
    asset_root: Path, package_dir: Path, asset_paths: tuple[str, ...]
) -> None:
    for asset_path in asset_paths:
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
                '    """Return the root directory containing asset subtrees."""',
                "    return Path(__file__).resolve().parent",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_setup_py(
    build_root: Path,
    repo_root: Path,
    version: str,
    distribution_name: str,
    module_name: str,
) -> None:
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
                f'    name="{distribution_name}",',
                f'    version="{version}",',
                '    author="EnvPool Contributors",',
                '    author_email="sail@sea.com",',
                '    description="Runtime data assets for EnvPool.",',
                '    long_description=open("README.md", encoding="utf-8").read(),',
                '    long_description_content_type="text/markdown",',
                '    url="https://github.com/Trinkle23897/envpool-assets",',
                f'    packages=find_namespace_packages(include=["{module_name}*"]),',
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


def _built_wheel(
    dist_dir: Path, distribution_name: str, version: str
) -> Path:
    wheel_prefix = distribution_name.replace("-", "_")
    matches = sorted(dist_dir.glob(f"{wheel_prefix}-{version}-*.whl"))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one {distribution_name} wheel in {dist_dir}, "
            f"found {matches}"
        )
    return matches[0]


def _check_wheel_contents(
    wheel_path: Path,
    module_name: str,
    asset_paths: tuple[str, ...],
    forbidden_paths: tuple[str, ...],
) -> None:
    with ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
    for asset_path in asset_paths:
        package_path = f"{module_name}/{asset_path}"
        if not any(
            name == package_path or name.startswith(f"{package_path}/")
            for name in names
        ):
            raise RuntimeError(f"Built wheel is missing {package_path}")
    for asset_path in forbidden_paths:
        package_path = f"{module_name}/{asset_path}"
        if package_path in names:
            raise RuntimeError(
                "Built wheel contains forbidden platform-specific file "
                f"{package_path}"
            )


def main() -> None:
    """Build the selected EnvPool asset wheel."""
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    config = PACKAGE_CONFIGS[args.package]
    distribution_name = str(config["distribution_name"])
    module_name = str(config["module_name"])
    asset_paths = config["asset_paths"]
    forbidden_paths = config["forbidden_paths"]
    assert isinstance(asset_paths, tuple)
    assert isinstance(forbidden_paths, tuple)
    asset_root = _validate_asset_root(
        args.asset_root, asset_paths, forbidden_paths
    )
    version = args.version

    with tempfile.TemporaryDirectory(prefix="envpool-assets-wheel-") as tmpdir:
        build_root = Path(tmpdir)
        package_dir = build_root / module_name
        _write_package_init(package_dir, version)
        _copy_assets(asset_root, package_dir, asset_paths)
        _write_setup_py(
            build_root, repo_root, version, distribution_name, module_name
        )
        _build_wheel(build_root, args.dist_dir)

    wheel_path = _built_wheel(args.dist_dir, distribution_name, version)
    _check_wheel_contents(
        wheel_path, module_name, asset_paths, forbidden_paths
    )
    print(wheel_path)


if __name__ == "__main__":
    main()
