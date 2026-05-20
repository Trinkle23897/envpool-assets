# envpool-assets

Runtime data assets for EnvPool.

This repository builds platform-independent data wheels. Platform-specific
executables and native libraries stay in the main `envpool` wheels.

Most assets are shipped in the main `envpool-assets` wheel. Asset groups that
would push that wheel over PyPI's file-size limit are split into their own
wheels. Every package has its own compatibility version; these versions are not
derived from the main `envpool` package version.

## Packages

```text
envpool-assets
envpool-assets-mujoco-large
envpool-assets-mujoco-playground-humanoid
```

## Build Locally

From this repository, with a checked-out EnvPool repository available:

```bash
python scripts/collect_envpool_assets.py \
  --envpool-root /path/to/envpool \
  --output-root .asset-root-base \
  --package base

python scripts/build_wheel.py \
  --asset-root .asset-root-base \
  --version 0.3.0 \
  --package base \
  --dist-dir dist

python scripts/optimize_wheel.py dist/envpool_assets-*.whl
```

If you already have an asset root with the EnvPool asset subtree layout, skip
collection and run only `scripts/build_wheel.py`.

## Expected Asset Root Layouts

The base package contains the smaller cross-family asset subtrees:

```text
base:              atari/roms
                   gfootball/assets
                   mujoco/assets_dmc
                   mujoco/assets_gym
                   mujoco/metaworld/assets
                   mujoco/robotics/assets
                   procgen/assets
                   vizdoom/bin/freedoom2.wad
                   vizdoom/maps
mujoco-large:      mujoco/myosuite/assets
                   mujoco/playground/assets/mujoco_playground/_src/locomotion/go1
                   mujoco/playground/assets/mujoco_playground/_src/locomotion/spot
                   mujoco/playground/assets/mujoco_playground/_src/manipulation/aero_hand
                   mujoco/playground/assets/mujoco_playground/_src/manipulation/aloha
                   mujoco/playground/assets/mujoco_playground/_src/manipulation/franka_emika_panda
                   mujoco/playground/assets/mujoco_playground/_src/manipulation/franka_emika_panda_robotiq
                   mujoco/playground/assets/mujoco_playground/_src/manipulation/leap_hand
                   mujoco/playground/assets/mujoco_menagerie/google_barkour_vb
                   mujoco/playground/assets/mujoco_menagerie/unitree_go1
                   mujoco/playground/assets/mujoco_menagerie/boston_dynamics_spot
                   mujoco/playground/assets/mujoco_menagerie/tetheria_aero_hand_open
                   mujoco/playground/assets/mujoco_menagerie/aloha
                   mujoco/playground/assets/mujoco_menagerie/franka_emika_panda
                   mujoco/playground/assets/mujoco_menagerie/robotiq_2f85_v4
                   mujoco/playground/assets/mujoco_menagerie/leap_hand
mujoco-playground-humanoid:
                   mujoco/playground/assets/mujoco_playground/_src/locomotion/apollo
                   mujoco/playground/assets/mujoco_playground/_src/locomotion/berkeley_humanoid
                   mujoco/playground/assets/mujoco_playground/_src/locomotion/g1
                   mujoco/playground/assets/mujoco_playground/_src/locomotion/h1
                   mujoco/playground/assets/mujoco_playground/_src/locomotion/op3
                   mujoco/playground/assets/mujoco_playground/_src/locomotion/t1
                   mujoco/playground/assets/mujoco_menagerie/apptronik_apollo
                   mujoco/playground/assets/mujoco_menagerie/berkeley_humanoid
                   mujoco/playground/assets/mujoco_menagerie/unitree_g1
                   mujoco/playground/assets/mujoco_menagerie/unitree_h1
                   mujoco/playground/assets/mujoco_menagerie/robotis_op3
                   mujoco/playground/assets/mujoco_menagerie/booster_t1
```

`vizdoom/bin/vizdoom` and `vizdoom/bin/vizdoom.pk3` are deliberately excluded
because they are platform-specific runtime files shipped by the main EnvPool
wheel.
