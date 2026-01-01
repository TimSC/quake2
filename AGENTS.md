# Quake2 Python Porting Notes

This repo is a work-in-progress port of the original Quake II C code to
Python. The unported reference lives in `quake2-original/`. We are focusing on
the ref_gl renderer and pygame based cross platform compatibility.

## Porting Approach
- Keep a 1:1 file mapping: `quake2-original/<path>.c` -> `<path>.py`.
- Preserve function order and names from C; avoid renaming or refactoring.
- Port logic incrementally: leave original C in triple-quoted blocks and
  translate the active logic directly below/around it.
- Favor structural fidelity over idiomatic Python so diffs are easy to follow.
- Low level audio code is mostly working, so probably doesn't need modification.

## Style Conventions (Observed)
- Keep the original copyright header at the top of each ported file.
- Use triple-quoted blocks to keep large C comment and code sections inline.
- C-style globals live at module scope and are initialized to `None` or a
  basic default, with type hints in comments.
- C structs become simple Python classes with fields initialized in `__init__`.
- Fixed-size C arrays become Python lists, often pre-filled in a `for` loop.
- Imports stay close to the C include order and the existing file patterns.

## Translation Patterns
- Pointers become object references or `None` (leave type comments intact).
- Integers and floats are kept explicit when needed; use `struct` for binary
  packing/unpacking.
- Constants and shared structs are pulled from `game/q_shared.py` and
-  `qcommon/qfiles.py`.
- Avoid `getattr` with a default of `None` just to suppress attribute errors;
  refer to the attribute directly so missing names raise immediately.
- Logging/errors flow through `qcommon/common.py` (e.g., `Com_Printf`,
  `Com_Error`) rather than `print` or exceptions.
- Vectors can be expressed as numpy arrays

## Practical Workflow
1. Locate the original C file in `quake2-original/`.
2. Create or open the matching `.py` file in the same relative path.
3. Paste the original C block (or keep existing block) in triple-quoted text.
4. Translate function-by-function, keeping names, order, and globals intact.
5. Use minimal Python features and avoid "cleanup" refactors.
6. Once the python function is ported, don't retain the original C function.
7. Commented out C code in python functions usually requires porting.
8. Don't enable or uncomment code that was disabled or commented out in the quake2-original C code.

## Dependencies
- Runtime dependencies are listed in `requirements.txt` and used throughout
  the port (notably `pygame`, `numpy`, and `PyOpenGL`).
