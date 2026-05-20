#!/usr/bin/env python3

"""Collect generated EnvPool assets from a source checkout."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

PackageConfig = tuple[tuple[str, ...], tuple[tuple[str, str], ...]]

_PLAYGROUND_TARGETS = (
    "//envpool/mujoco:gen_mujoco_playground_assets",
    "//envpool/mujoco:gen_mujoco_playground_menagerie",
)


def _playground_source_path(source_path: str) -> tuple[str, str]:
    return (
        "envpool/mujoco/playground/assets/mujoco_playground/_src/"
        f"{source_path}",
        "mujoco/playground/assets/mujoco_playground/_src/"
        f"{source_path}",
    )


def _playground_menagerie_path(robot_path: str) -> tuple[str, str]:
    return (
        "envpool/mujoco/playground/assets/mujoco_menagerie/"
        f"{robot_path}",
        "mujoco/playground/assets/mujoco_menagerie/"
        f"{robot_path}",
    )


def _playground_package(
    source_paths: tuple[str, ...],
    menagerie_paths: tuple[str, ...],
) -> PackageConfig:
    mappings = [_playground_source_path(path) for path in source_paths]
    mappings.extend(
        _playground_menagerie_path(path) for path in menagerie_paths
    )
    return _PLAYGROUND_TARGETS, tuple(mappings)

PACKAGE_CONFIGS: dict[str, PackageConfig] = {
    "base": (
        (
            "//envpool/atari:gen_atari_roms",
            "//envpool/gfootball:gen_gfootball_assets_data",
            "//envpool/gfootball:gen_gfootball_assets_fonts",
            "//envpool/mujoco:gen_mujoco_dmc_xml",
            "//envpool/mujoco:gen_mujoco_gym_xml",
            "//envpool/mujoco:gen_metaworld_assets",
            "//envpool/mujoco:gen_gymnasium_robotics_assets",
            "//envpool/procgen:gen_procgen_assets",
            "//envpool/vizdoom:gen_vizdoom_maps",
            "//envpool/vizdoom/bin:freedoom",
        ),
        (
            ("envpool/atari/roms", "atari/roms"),
            ("envpool/gfootball/assets/data", "gfootball/assets/data"),
            ("envpool/gfootball/assets/fonts", "gfootball/assets/fonts"),
            ("envpool/mujoco/assets_dmc", "mujoco/assets_dmc"),
            ("envpool/mujoco/assets_gym", "mujoco/assets_gym"),
            ("envpool/mujoco/metaworld/assets", "mujoco/metaworld/assets"),
            ("envpool/mujoco/robotics/assets", "mujoco/robotics/assets"),
            ("envpool/procgen/assets", "procgen/assets"),
            ("envpool/vizdoom/bin/freedoom2.wad", "vizdoom/bin/freedoom2.wad"),
            ("envpool/vizdoom/maps", "vizdoom/maps"),
        ),
    ),
    "mujoco-large": (
        ("//envpool/mujoco:gen_myosuite_assets", *_PLAYGROUND_TARGETS),
        (
            ("envpool/mujoco/myosuite/assets", "mujoco/myosuite/assets"),
            _playground_source_path("locomotion/go1"),
            _playground_source_path("locomotion/spot"),
            _playground_source_path("manipulation/aero_hand"),
            _playground_source_path("manipulation/aloha"),
            _playground_source_path("manipulation/franka_emika_panda"),
            _playground_source_path("manipulation/franka_emika_panda_robotiq"),
            _playground_source_path("manipulation/leap_hand"),
            _playground_menagerie_path("google_barkour_vb"),
            _playground_menagerie_path("unitree_go1"),
            _playground_menagerie_path("boston_dynamics_spot"),
            _playground_menagerie_path("tetheria_aero_hand_open"),
            _playground_menagerie_path("aloha"),
            _playground_menagerie_path("franka_emika_panda"),
            _playground_menagerie_path("robotiq_2f85_v4"),
            _playground_menagerie_path("leap_hand"),
        ),
    ),
    "mujoco-playground-humanoid": _playground_package(
        (
            "locomotion/apollo",
            "locomotion/berkeley_humanoid",
            "locomotion/g1",
            "locomotion/h1",
            "locomotion/op3",
            "locomotion/t1",
        ),
        (
            "apptronik_apollo",
            "berkeley_humanoid",
            "unitree_g1",
            "unitree_h1",
            "robotis_op3",
            "booster_t1",
        ),
    ),
}


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
        "--package",
        choices=sorted(PACKAGE_CONFIGS),
        required=True,
        help="Asset package profile to collect.",
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


def _run_bazel(
    envpool_root: Path, bazel: str, targets: tuple[str, ...]
) -> None:
    command = [
        bazel,
        "build",
        "--config=release",
        "--define=envpool_release_assets=true",
        *targets,
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


def _copy_outputs(
    envpool_root: Path,
    output_root: Path,
    output_mappings: tuple[tuple[str, str], ...],
) -> None:
    bazel_bin = envpool_root / "bazel-bin"
    if not bazel_bin.exists():
        raise FileNotFoundError(f"bazel-bin not found: {bazel_bin}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    for source_rel, dest_rel in output_mappings:
        _copy_path(bazel_bin / source_rel, output_root / dest_rel)


def main() -> None:
    """Collect EnvPool assets into a standalone asset root."""
    args = _parse_args()
    envpool_root = args.envpool_root.resolve()
    output_root = args.output_root.resolve()
    bazel_targets, output_mappings = PACKAGE_CONFIGS[args.package]
    if not args.skip_bazel:
        _prepare_envpool_requirements(envpool_root)
        _run_bazel(envpool_root, args.bazel, bazel_targets)
    _copy_outputs(envpool_root, output_root, output_mappings)
    print(output_root)


if __name__ == "__main__":
    main()
