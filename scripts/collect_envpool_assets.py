#!/usr/bin/env python3

"""Collect generated EnvPool assets from a source checkout."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

BAZEL_TARGETS = (
    "//envpool/atari:gen_atari_roms",
    "//envpool/gfootball:gen_gfootball_assets_data",
    "//envpool/gfootball:gen_gfootball_assets_fonts",
    "//envpool/mujoco:gen_mujoco_dmc_xml",
    "//envpool/mujoco:gen_mujoco_gym_xml",
    "//envpool/mujoco:gen_gymnasium_robotics_assets",
    "//envpool/mujoco:gen_metaworld_assets",
    "//envpool/mujoco:gen_myosuite_assets",
    "//envpool/procgen:gen_procgen_assets",
    "//envpool/vizdoom:gen_vizdoom_maps",
    "//envpool/vizdoom/bin:freedoom",
)

OUTPUT_MAPPINGS = (
    ("envpool/atari/roms", "atari/roms"),
    ("envpool/gfootball/assets/data", "gfootball/assets/data"),
    ("envpool/gfootball/assets/fonts", "gfootball/assets/fonts"),
    ("envpool/mujoco/assets_dmc", "mujoco/assets_dmc"),
    ("envpool/mujoco/assets_gym", "mujoco/assets_gym"),
    ("envpool/mujoco/metaworld/assets", "mujoco/metaworld/assets"),
    ("envpool/mujoco/myosuite/assets", "mujoco/myosuite/assets"),
    ("envpool/mujoco/robotics/assets", "mujoco/robotics/assets"),
    ("envpool/procgen/assets", "procgen/assets"),
    ("envpool/vizdoom/bin/freedoom2.wad", "vizdoom/bin/freedoom2.wad"),
    ("envpool/vizdoom/maps", "vizdoom/maps"),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--envpool-root",
        type=Path,
        required=True,
        help="EnvPool source checkout.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Directory where the collected asset root should be written.",
    )
    parser.add_argument(
        "--bazel",
        default="bazelisk",
        help="Bazel executable to run. Defaults to bazelisk.",
    )
    parser.add_argument(
        "--skip-bazel",
        action="store_true",
        help="Only copy already-built outputs from bazel-bin.",
    )
    return parser.parse_args()


def _run_bazel(envpool_root: Path, bazel: str) -> None:
    command = [
        bazel,
        "build",
        "--config=release",
        "--define=envpool_release_assets=true",
        *BAZEL_TARGETS,
    ]
    subprocess.run(command, cwd=envpool_root, check=True)


def _prepare_envpool_requirements(envpool_root: Path) -> None:
    requirements_dir = envpool_root / "third_party" / "pip_requirements"
    requirements = requirements_dir / "requirements.txt"
    release_lock = requirements_dir / "requirements-release-lock.txt"
    if requirements.exists():
        return
    if not release_lock.is_file():
        raise FileNotFoundError(
            f"EnvPool release requirements lock not found: {release_lock}"
        )
    shutil.copy2(release_lock, requirements)


def _copy_path(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Expected Bazel output does not exist: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, symlinks=False)
    else:
        shutil.copy2(src, dst)


def _copy_outputs(envpool_root: Path, output_root: Path) -> None:
    bazel_bin = envpool_root / "bazel-bin"
    if not bazel_bin.exists():
        raise FileNotFoundError(f"bazel-bin not found: {bazel_bin}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    for source_rel, dest_rel in OUTPUT_MAPPINGS:
        _copy_path(bazel_bin / source_rel, output_root / dest_rel)


def main() -> None:
    """Collect EnvPool assets into a standalone asset root."""
    args = _parse_args()
    envpool_root = args.envpool_root.resolve()
    output_root = args.output_root.resolve()
    if not args.skip_bazel:
        _prepare_envpool_requirements(envpool_root)
        _run_bazel(envpool_root, args.bazel)
    _copy_outputs(envpool_root, output_root)
    print(output_root)


if __name__ == "__main__":
    main()
