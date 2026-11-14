"""MiroFish CLI.

Usage:
    python3 -m mirofish validate [dir]
    python3 -m mirofish list
    python3 -m mirofish cost --agents N [--tier cheap|frontier]
    python3 -m mirofish manifest --run-id X

All sibling-module imports are guarded so the CLI stays usable while the
rest of the package is still being built.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
REPO_ROOT = PKG_DIR.parent


def _err(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 1


def _platform_dirs() -> list[Path]:
    candidates = [
        REPO_ROOT / "platforms",
        PKG_DIR / "platforms",
        Path.cwd() / "platforms",
    ]
    seen, dirs = set(), []
    for d in candidates:
        try:
            key = d.resolve()
        except OSError:
            key = d
        if d.is_dir() and key not in seen:
            seen.add(key)
            dirs.append(d)
    return dirs


def _load_cost_model():
    """Import calibration/cost_model.py directly, bypassing the package
    __init__ (which may pull in numpy-dependent siblings)."""
    path = PKG_DIR / "calibration" / "cost_model.py"
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found")
    spec = importlib.util.spec_from_file_location("mirofish_cost_model", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ImportError:
        raise RuntimeError(
            "pyyaml is not installed; install it (pip install pyyaml) or vendor it"
        ) from None
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------
# subcommands
# --------------------------------------------------------------------------

def cmd_validate(args) -> int:
    """Run core.validate.validate_directory on a spec directory."""
    if args.dir:
        target = Path(args.dir).expanduser().resolve()
    else:
        # default: platforms/ spec dir if present, else repo root
        target = REPO_ROOT / "platforms"
        if not target.is_dir():
            target = REPO_ROOT
    if not target.is_dir():
        return _err(f"not a directory: {target}")

    validate_directory = None
    try:
        from mirofish.core.validate import validate_directory as vd  # type: ignore
        validate_directory = vd
    except Exception:
        pass
    if validate_directory is None:
        # fallback: core/ may live at repo root outside the package
        sys.path.insert(0, str(REPO_ROOT))
        try:
            from core.validate import validate_directory as vd  # type: ignore
            validate_directory = vd
        except Exception as exc:
            return _err(
                "core.validate.validate_directory is unavailable "
                f"({exc.__class__.__name__}: {exc}); "
                "the validation module is not implemented yet"
            )
        finally:
            sys.path.remove(str(REPO_ROOT))

    try:
        results = validate_directory(str(target))
    except Exception as exc:
        return _err(f"validation failed: {exc}")

    # results: {filename: [ValidationIssue, ...]} (or a flat list on older impls)
    if isinstance(results, dict):
        total = sum(len(v) for v in results.values())
        if total == 0:
            print(f"OK: no issues found in {target} "
                  f"({len(results)} file(s) checked)")
            return 0
        print(f"{total} issue(s) across {len(results)} file(s) in {target}:")
        rc = 0
        for filename, issues in results.items():
            for issue in issues:
                sev = getattr(issue, "severity", "?")
                code = getattr(issue, "code", "?")
                loc = getattr(issue, "path", "?")
                msg = getattr(issue, "message", str(issue))
                print(f"  [{sev}] {filename}:{loc} {code}: {msg}")
                if sev == "error":
                    rc = 1
        return rc

    # flat iterable fallback
    issues = list(results)
    if not issues:
        print(f"OK: no issues found in {target}")
        return 0
    print(f"{len(issues)} issue(s) in {target}:")
    for issue in issues:
        print(f"  - {issue}")
    return 1


def cmd_list(args) -> int:
    """List registered platforms from platforms/*.yaml."""
    dirs = _platform_dirs()
    if not dirs:
        return _err(f"no platforms/ directory found (looked under {REPO_ROOT})")

    found = False
    for d in dirs:
        for path in sorted(d.glob("*.yaml")) + sorted(d.glob("*.yml")):
            found = True
            try:
                spec = _load_yaml(path) or {}
            except Exception as exc:
                print(f"{path.name}: <unparseable: {exc}>")
                continue
            pid = spec.get("platform_id") or path.stem
            name = spec.get("display_name") or "-"
            arch = spec.get("archetype") or "-"
            tier = spec.get("privacy_tier") or "-"
            ver = spec.get("spec_version") or "-"
            print(f"{pid:12} {name:28} archetype={arch:22} privacy={tier:8} spec={ver}  ({path})")
    if not found:
        return _err(f"no platform specs (*.yaml) found in {dirs}")
    return 0


def cmd_cost(args) -> int:
    """Print an LLM cost estimate for a population size."""
    try:
        try:
            from mirofish.calibration.cost_model import estimate_cost  # type: ignore
        except Exception:
            estimate_cost = _load_cost_model().estimate_cost
    except Exception as exc:
        return _err(f"cost_model unavailable: {exc}")

    try:
        est = estimate_cost(
            args.agents,
            steps_per_day=args.steps_per_day,
            activation_rate=args.activation,
            productive_rate=args.productive,
            model_tier=args.tier,
        )
    except ValueError as exc:
        return _err(str(exc))

    print(f"population:            {est['population']:,}")
    print(f"model_tier:            {est['model_tier']}")
    print(f"calls_per_day:         {est['calls_per_day']:,.0f}")
    print(f"tokens_per_day:        {est['tokens_per_day']:,.0f}")
    print(f"monthly_llm_cost_usd:  ${est['monthly_llm_cost_usd']:,.2f}")
    print(f"cost_per_action_usd:   ${est['cost_per_action_usd']:.6f}")
    if est["emergent_floor_warning"]:
        print(f"warning:               {est['emergent_floor_warning']}")
    return 0


def cmd_manifest(args) -> int:
    """Create a run-manifest skeleton for a run id."""
    run_id = args.run_id
    out_dir = Path(args.out).expanduser() if args.out else Path.cwd() / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"

    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mirofish_version": _pkg_version(),
        "platforms": _platform_ids(),
        "config": {
            "population": None,
            "steps_per_day": 24,
            "activation_rate": 0.10,
            "productive_rate": 0.10,
            "model_tier": "cheap",
        },
        "artifacts": {},
        "status": "skeleton",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path}")
    return 0


def _pkg_version() -> str:
    try:
        from mirofish import __version__
        return __version__
    except Exception:
        return "unknown"


def _platform_ids() -> list[str]:
    ids = []
    for d in _platform_dirs():
        for path in sorted(d.glob("*.yaml")):
            try:
                spec = _load_yaml(path) or {}
                ids.append(spec.get("platform_id") or path.stem)
            except Exception:
                ids.append(path.stem)
    return ids


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mirofish",
        description="MiroFish: declarative multi-platform social simulation",
    )
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate platform specs in a directory")
    v.add_argument("dir", nargs="?", default=None,
                   help="directory to validate (default: repo root)")
    v.set_defaults(func=cmd_validate)

    sub.add_parser("list", help="list registered platforms").set_defaults(func=cmd_list)

    c = sub.add_parser("cost", help="estimate monthly LLM cost")
    c.add_argument("--agents", type=int, required=True, help="population size")
    c.add_argument("--tier", choices=["cheap", "frontier"], default="cheap")
    c.add_argument("--steps-per-day", type=int, default=24)
    c.add_argument("--activation", type=float, default=0.10)
    c.add_argument("--productive", type=float, default=0.10)
    c.set_defaults(func=cmd_cost)

    m = sub.add_parser("manifest", help="create a run manifest skeleton")
    m.add_argument("--run-id", required=True)
    m.add_argument("--out", default=None, help="output dir (default: ./runs/<run-id>)")
    m.set_defaults(func=cmd_manifest)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except BrokenPipeError:
        return 0
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
