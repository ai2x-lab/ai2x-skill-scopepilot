---
name: scope-scpi-automation
description: Control oscilloscopes over SCPI/VISA for basic automation tasks including connectivity checks, channel display on/off, vertical scale changes, basic measurements, and log collection. Use when Codex needs a reusable oscilloscope control workflow that can be extended with vendor-specific command profiles.
---

# Scope SCPI Automation

Use `scripts/scope_cli.py` as the primary entrypoint. Do not generate raw SCPI unless the profile system is missing a required command.

## Workflow

1. List profiles with `--list-profiles` if vendor support is unclear.
2. List VISA resources with `--list` if the resource string is unknown.
3. Use `identify` first when connecting to a new instrument.
4. Run `run`, `stop`, `set-display`, `set-scale`, `set-time-scale`, `measure`, `capture`, or `toggle-sequence` through the CLI.
5. Capture logs with `--log-file` or `--json-log-file` for traceability.

## Constraints

- Prefer `--pyvisa-py` when no vendor VISA backend is installed.
- Keep vendor differences in `vendor_profiles/*.json`.
- Use channel indices like `1`, `2`, `3`, `4`; let the profile format the real channel name.
- Treat vertical and time scales as legal stepped values, not arbitrary floats. Put vendor scale rules in `scale_rules`.
- If a command fails for one vendor, update the vendor profile before changing core logic.

## References

- Profile format: `references/profile-spec.md`
