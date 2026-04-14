# envpool-assets

Runtime data assets for EnvPool.

This package intentionally contains only platform-independent data files. The
resulting wheel should be a single `py3-none-any` artifact, so it does not need
a Python-version or platform build matrix. Platform-specific executables and
native libraries stay in the main `envpool` wheels.

## Build locally

From a checked-out EnvPool repository:

```bash
python scripts/collect_envpool_assets.py \
  --envpool-root /path/to/envpool \
  --output-root .asset-root

python scripts/build_wheel.py \
  --asset-root .asset-root \
  --envpool-root /path/to/envpool \
  --dist-dir dist
```

If you already have an asset root with the EnvPool asset subtree layout, skip
collection and run only `scripts/build_wheel.py`.

## Expected asset root layout

The asset root must contain these paths:

```text
atari/roms
gfootball/assets
mujoco/assets_dmc
mujoco/assets_gym
mujoco/metaworld/assets
mujoco/robotics/assets
procgen/assets
vizdoom/bin/freedoom2.wad
vizdoom/maps
```

`vizdoom/bin/vizdoom` and `vizdoom/bin/vizdoom.pk3` are deliberately excluded
because they are platform-specific runtime files shipped by the main EnvPool
wheel.

