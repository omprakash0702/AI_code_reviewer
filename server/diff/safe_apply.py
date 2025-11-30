# server/diff/safe_apply.py
import re

def safe_apply_patch(original_code: str, patch_text: str):
    if not patch_text.strip():
        return {
            "success": False,
            "patched_code": original_code,
            "error": "Empty patch"
        }

    try:
        orig_lines = original_code.splitlines(keepends=True)
        patch_lines = patch_text.splitlines(keepends=False)

        # Extract hunks
        hunks = []
        current_hunk = []

        for line in patch_lines:
            if line.startswith("@@"):
                if current_hunk:
                    hunks.append(current_hunk)
                current_hunk = [line]
            elif current_hunk:
                current_hunk.append(line)

        if current_hunk:
            hunks.append(current_hunk)

        # If no hunks were found → AI sent wrong diff format
        if not hunks:
            return {
                "success": False,
                "patched_code": original_code,
                "error": "No hunks found in patch"
            }

        out = []
        orig_index = 0

        for hunk in hunks:
            # Parse hunk header
            header = hunk[0]
            m = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", header)
            if not m:
                return {
                    "success": False,
                    "patched_code": original_code,
                    "error": "Invalid hunk header"
                }

            old_start = int(m.group(1)) - 1

            # Add code before hunk
            while orig_index < old_start:
                out.append(orig_lines[orig_index])
                orig_index += 1

            # Apply hunk body
            for line in hunk[1:]:
                if line.startswith(" "):
                    out.append(orig_lines[orig_index])
                    orig_index += 1
                elif line.startswith("-"):
                    orig_index += 1
                elif line.startswith("+"):
                    content = line[1:] + "\n"
                    out.append(content)

        # Add remaining lines
        while orig_index < len(orig_lines):
            out.append(orig_lines[orig_index])
            orig_index += 1

        return {
            "success": True,
            "patched_code": "".join(out),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "patched_code": original_code,
            "error": str(e)
        }
