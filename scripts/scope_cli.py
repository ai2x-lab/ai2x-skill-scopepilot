from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from logger import ActionLogger
from profile_loader import available_profiles, load_profile
from scope_core import ScopeSession, open_resource_manager


def parse_backend(args: argparse.Namespace) -> str | None:
    if args.pyvisa_py and not args.backend:
        return "@py"
    return args.backend


def parse_channels(channel_text: str) -> list[int]:
    channels: list[int] = []
    for item in channel_text.split(","):
        value = item.strip()
        if not value:
            continue
        channels.append(int(value))
    return channels


def parse_scales(scale_text: str) -> list[float]:
    scales: list[float] = []
    for item in scale_text.split(","):
        value = item.strip()
        if not value:
            continue
        scales.append(float(value))
    return scales


def create_logger(args: argparse.Namespace) -> ActionLogger:
    text_path = Path(args.log_file) if args.log_file else None
    json_path = Path(args.json_log_file) if args.json_log_file else None
    return ActionLogger(text_log_path=text_path, json_log_path=json_path)


def list_resources(backend: str | None) -> int:
    rm = open_resource_manager(backend)
    try:
        resources = rm.list_resources()
        print("Detected VISA resources:")
        for item in resources:
            print(f"  - {item}")
        if not resources:
            print("  <none>")
        return 0
    finally:
        rm.close()


def run_identify(args: argparse.Namespace, logger: ActionLogger) -> int:
    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        idn = scope.identify()
        print(idn)
        logger.finalize({"status": "ok", "action": "identify", "idn": idn})
        return 0
    finally:
        scope.close()


def run_set_display(args: argparse.Namespace, logger: ActionLogger) -> int:
    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        enabled = args.state.lower() == "on"
        scope.set_channel_display(args.channel, enabled)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "action": "set-display",
                    "channel": args.channel,
                    "enabled": enabled,
                }
            )
        )
        logger.finalize({"status": "ok", "action": "set-display"})
        return 0
    finally:
        scope.close()


def run_set_scale(args: argparse.Namespace, logger: ActionLogger) -> int:
    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        applied = scope.set_vertical_scale(args.channel, args.scale)
        print(json.dumps({"status": "ok", "action": "set-scale", "channel": args.channel, "requested_scale": args.scale, "applied_scale": applied}))
        logger.finalize({"status": "ok", "action": "set-scale"})
        return 0
    finally:
        scope.close()


def run_set_time_scale(args: argparse.Namespace, logger: ActionLogger) -> int:
    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        applied = scope.set_time_scale(args.scale)
        print(json.dumps({"status": "ok", "action": "set-time-scale", "requested_scale": args.scale, "applied_scale": applied}))
        logger.finalize({"status": "ok", "action": "set-time-scale"})
        return 0
    finally:
        scope.close()


def run_measure(args: argparse.Namespace, logger: ActionLogger) -> int:
    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        value = scope.measure(args.channel, args.item)
        result = {
            "status": "ok",
            "action": "measure",
            "channel": args.channel,
            "item": args.item,
            "value": value,
        }
        print(json.dumps(result))
        logger.finalize(result)
        return 0
    finally:
        scope.close()


def run_toggle_sequence(args: argparse.Namespace, logger: ActionLogger) -> int:
    channels = parse_channels(args.channels)
    scales = parse_scales(args.scales)
    if not channels:
        raise ValueError("No channels provided.")
    if not scales:
        raise ValueError("No scales provided.")

    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        for cycle in range(args.cycles):
            for offset, channel in enumerate(channels):
                scale = scales[(cycle + offset) % len(scales)]
                scope.set_vertical_scale(channel, scale)
                scope.set_channel_display(channel, True)
                time.sleep(args.interval)
                scope.set_channel_display(channel, False)
                time.sleep(args.interval)

        result = {
            "status": "ok",
            "action": "toggle-sequence",
            "channels": channels,
            "scales": scales,
            "cycles": args.cycles,
            "interval": args.interval,
        }
        print(json.dumps(result))
        logger.finalize(result)
        return 0
    finally:
        scope.close()


def run_run(args: argparse.Namespace, logger: ActionLogger) -> int:
    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        scope.run_acquisition()
        result = {"status": "ok", "action": "run"}
        print(json.dumps(result))
        logger.finalize(result)
        return 0
    finally:
        scope.close()


def run_stop(args: argparse.Namespace, logger: ActionLogger) -> int:
    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        scope.stop_acquisition()
        result = {"status": "ok", "action": "stop"}
        print(json.dumps(result))
        logger.finalize(result)
        return 0
    finally:
        scope.close()


def run_capture(args: argparse.Namespace, logger: ActionLogger) -> int:
    profile = load_profile(args.profile)
    scope = ScopeSession(
        resource_name=args.resource,
        profile_name=args.profile,
        profile=profile,
        visa_backend=parse_backend(args),
        timeout_ms=args.timeout_ms,
        logger=logger,
    )
    try:
        saved_path = scope.capture_screenshot(args.output)
        result = {"status": "ok", "action": "capture", "output": saved_path}
        print(json.dumps(result))
        logger.finalize(result)
        return 0
    finally:
        scope.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Profile-driven oscilloscope SCPI control CLI."
    )
    parser.add_argument("--resource", help="VISA resource string.")
    parser.add_argument("--profile", default="common", help="Vendor profile name.")
    parser.add_argument("--backend", help='Optional VISA backend, such as "@py".')
    parser.add_argument("--pyvisa-py", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=5000)
    parser.add_argument("--log-file", help="Append newline-delimited JSON events.")
    parser.add_argument("--json-log-file", help="Write final JSON summary file.")
    parser.add_argument("--list", action="store_true", help="List VISA resources.")
    parser.add_argument(
        "--list-profiles", action="store_true", help="List available vendor profiles."
    )

    subparsers = parser.add_subparsers(dest="command")

    identify = subparsers.add_parser("identify")
    identify.set_defaults(handler=run_identify)

    set_display = subparsers.add_parser("set-display")
    set_display.add_argument("--channel", type=int, required=True)
    set_display.add_argument("--state", choices=["on", "off"], required=True)
    set_display.set_defaults(handler=run_set_display)

    set_scale = subparsers.add_parser("set-scale")
    set_scale.add_argument("--channel", type=int, required=True)
    set_scale.add_argument("--scale", type=float, required=True)
    set_scale.set_defaults(handler=run_set_scale)

    set_time_scale = subparsers.add_parser("set-time-scale")
    set_time_scale.add_argument("--scale", type=float, required=True)
    set_time_scale.set_defaults(handler=run_set_time_scale)

    measure = subparsers.add_parser("measure")
    measure.add_argument("--channel", type=int, required=True)
    measure.add_argument(
        "--item",
        choices=["vpp", "frequency", "vrms"],
        required=True,
    )
    measure.set_defaults(handler=run_measure)

    toggle = subparsers.add_parser("toggle-sequence")
    toggle.add_argument("--channels", default="1,2,3,4")
    toggle.add_argument("--scales", default="0.1,0.2,0.5,1.0")
    toggle.add_argument("--interval", type=float, default=5.0)
    toggle.add_argument("--cycles", type=int, default=1)
    toggle.set_defaults(handler=run_toggle_sequence)

    run_parser = subparsers.add_parser("run")
    run_parser.set_defaults(handler=run_run)

    stop_parser = subparsers.add_parser("stop")
    stop_parser.set_defaults(handler=run_stop)

    capture = subparsers.add_parser("capture")
    capture.add_argument("--output", required=True)
    capture.set_defaults(handler=run_capture)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_profiles:
        print("\n".join(available_profiles()))
        return 0

    if args.list:
        return list_resources(parse_backend(args))

    if not args.resource:
        parser.print_help(sys.stderr)
        print("\nError: --resource is required unless --list or --list-profiles is used.")
        return 1

    if not hasattr(args, "handler"):
        parser.print_help(sys.stderr)
        print("\nError: command is required.")
        return 1

    logger = create_logger(args)
    try:
        return args.handler(args, logger)
    except Exception as exc:
        logger.log("error", message=str(exc))
        logger.finalize({"status": "error", "message": str(exc)})
        print(f"ERROR: {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
