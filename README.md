# Retrace + Requests Quickstart (matches `footest13` structure)

This folder contains `test.py` (requests demo) and instructions to record/replay with Retrace in the same layout we use locally

## Prerequisites

- macOS with VS Code (for the debug view).
- Python 3.11.
- Packages:
  ```bash
  python -m pip install --upgrade pip
  python -m pip install retracesoftware-autoenable-debug requests PyYAML
  ```
- Enable Retrace (one-time per env):
  ```bash
  python -m retracesoftware.autoenable
  ```

## Record

From the folder containing `test.py` (e.g., this folder):

```bash
# RETRACE_STACKTRACES is optional; omit for a cleaner demo
RETRACE=1 RETRACE_RECORDING_PATH=recording \
python test.py
```

After this run you’ll have `recording/` with:

- `replay.code-workspace`
- `run/test.py`
- `settings.json`
- `trace.bin`

## Replay (CLI)

From `recording/run`:

```bash
python -m retracesoftware --recording ..
```

(`..` points to the recording root.)

## Replay with VS Code

1. Open VS Code → File → “Open Workspace from File…” → select `recording/replay.code-workspace`.
2. In the explorer you’ll see `recording/` and `run/`. Open `run/test.py`.
3. Add breakpoints at useful spots:
   - After each fetch (inspect `user_name`, `post_title`, `todo_title`).
   - After the forced retry (inspect `retry_status`, `retry_attempts`).
   - If you run with `--trigger-bug`, set a breakpoint on the ZeroDivisionError to replay into the crash state.
4. Run → Start Debugging. Step through; replay should hit the same breakpoints with recorded responses (no live network needed).

## Run normally (no Retrace)

```bash
python test.py
```

## Optional: trigger a bug to replay into

Use `--trigger-bug` with record/replay to generate a deliberate ZeroDivisionError and inspect state during replay:

```bash
RETRACE=1 RETRACE_RECORDING_PATH=recording python test.py --trigger-bug
```

## Notes

- Run `python -m retracesoftware.autoenable` once per env to install the sitecustomize hook.
- `RETRACE=1` activates Retrace when you run; `RETRACE_RECORDING_PATH` is your capture folder—reuse it for replay.
- The retry path is simulated: first attempt fails, second succeeds, so you can step through error/retry handling without flaky endpoints.
