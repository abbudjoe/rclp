# Contributing

This is an experimental protocol MVP. Contributions should keep the protocol narrow and testable.

Before opening a PR:

```bash
python -m compileall src tests
python -m pytest
```

If the Rust toolchain is installed:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

Keep docs precise: RCLP is a safety-adjacent authority layer and protocol MVP,
not a certified safety system or hosted commercial platform.

Do not add commercial platform code to this repo.
