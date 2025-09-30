import argparse
import glob
import os
import re

import ass
import ass.data


def normalize_time(value: str) -> str:
    """
    Normalize ASS time format to H:MM:SS.CS (centiseconds).
    Accepts inputs like:
      0:04:03.1   -> 0:04:03.10
      0:04:03.100 -> 0:04:03.10
      0:04:03     -> 0:04:03.00
    """
    m = re.fullmatch(r"(\d+):(\d{2}):(\d{2})(?:\.(\d{1,3}))?", value.strip())
    if not m:
        return "0:00:00.00"

    h, mnt, sec, frac = m.groups()
    if frac is None:
        frac = "00"
    elif len(frac) == 1:
        frac = frac + "0"  # "1" → "10"
    elif len(frac) == 2:
        pass  # already ok
    elif len(frac) == 3:
        frac = frac[:2]  # truncate milliseconds → centiseconds
    else:
        frac = "00"

    return f"{int(h)}:{mnt}:{sec}.{frac}"


def is_valid_time(value: str) -> bool:
    # Matches ASS timestamp: H:MM:SS.CS (centiseconds)
    return bool(re.fullmatch(r"\d+:\d{2}:\d{2}\.\d{2}", value))


def is_integer(value: str) -> bool:
    return bool(re.fullmatch(r"\d+", value))


def fix_closedcaptionconverter(input_path, output_path):
    with open(input_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    # Check for "closedcaptionconverter" inside [Script Info]
    inside_script_info = False
    found_marker = False
    for line in lines:
        if line.strip().lower().startswith("[script info]"):
            inside_script_info = True
            continue
        if inside_script_info and line.strip().startswith("["):
            break
        if "closedcaptionconverter" in line.lower():
            found_marker = True
            break

    if not found_marker:
        return False

    fixed_lines = []
    in_events = False

    for line in lines:
        if line.strip().startswith("[Events]"):
            in_events = True
            fixed_lines.append(line)
            continue

        if in_events and line.startswith("Dialogue:"):
            prefix, rest = line.split(":", 1)
            parts = rest.split(",", 9)

            # Normalize split length
            if len(parts) < 10:
                parts += [""] * (10 - len(parts))
            elif len(parts) > 10:
                text = ",".join(parts[9:])
                parts = parts[:9] + [text]

            layer, start, end, style, name, mL, mR, mV, effect, text = [p.strip() for p in parts]

            fixed = False

            # Layer must be int
            if not layer.isdigit():
                layer = "0"
                fixed = True

            # Time must match ASS format
            if not is_valid_time(start):
                start = normalize_time(start)
                fixed = True
            if not is_valid_time(end):
                end = normalize_time(end)
                fixed = True

            # Margins → must be integers
            if not is_integer(mL):
                mL, fixed = "0", True
            if not is_integer(mR):
                mR, fixed = "0", True
            if not is_integer(mV):
                mV, fixed = "0", True

            # Effect allowed empty
            if effect == "":
                pass

            fixed_line = f"{prefix}:{layer},{start},{end},{style},{name},{mL},{mR},{mV},{effect},{text}"

            if fixed:
                fixed_lines.append(fixed_line + "\n")
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.writelines(fixed_lines)
        return True


def remove_embedded_fonts(doc: ass.Document):
    allowed_sections = {
        "script info",
        "aegisub project garbage",
        "v4+ styles",
        "graphics",
        "events",
        "aegisub extradata",
    }

    # Find sections not in allowed list (case-insensitive)
    to_remove = [name for name in doc.sections.keys() if name.lower() not in allowed_sections]

    for name in to_remove:
        del doc.sections[name]


def remove_unused_styles(doc: ass.Document, is_replace_font=False, is_fucking_ccc_sub=False):
    used_styles = set(event.style for event in doc.events if isinstance(event, ass.Dialogue))
    doc.styles = [style for style in doc.styles if style.name in used_styles]
    if is_replace_font:
        doc.info["PlayResX"] = "1920"
        doc.info["PlayResY"] = "1080"
        doc.info["ScaledBorderAndShadow"] = "Yes"
        fucking_ccc_styles = [
            "TopLeft",
            "TopCenter",
            "TopRight",
            "CenterLeft",
            "CenterCenter",
            "CenterRight",
            "BottomLeft",
            "BottomCenter",
            "BottomRight",
        ]

        for style in doc.styles:
            if (
                is_fucking_ccc_sub
                and style.name in fucking_ccc_styles
                and "monospace" in style.fontname
                and style.fontsize == 16
            ):
                style.fontname = "UVN Sach Vo"
                style.fontsize = 81
                style.primary_color = ass.data.Color.from_ass("&H00FFFFFF")
                style.secondary_color = ass.data.Color.from_ass("&H00000000")
                style.outline_color = ass.data.Color.from_ass("&H4D000000")
                style.back_color = ass.data.Color.from_ass("&HBC000000")
                style.bold = True
                style.italic = False
                style.underline = False
                style.strike_out = False
                style.scale_x = 80
                style.scale_y = 100
                style.spacing = 0
                style.angle = 0
                style.border_style = 1
                style.outline = 3
                style.shadow = 3
                style.margin_l = 60
                style.margin_r = 60
                style.margin_v = 50
                style.encoding = 1

            if style.name == "Default" and style.fontname == "Arial Unicode MS" and style.fontsize == 20:
                style.fontname = "UVN Sach Vo"
                style.fontsize = 81
                style.primary_color = ass.data.Color.from_ass("&H00FFFFFF")
                style.secondary_color = ass.data.Color.from_ass("&H00000000")
                style.outline_color = ass.data.Color.from_ass("&H4D000000")
                style.back_color = ass.data.Color.from_ass("&HBC000000")
                style.bold = True
                style.italic = False
                style.underline = False
                style.strike_out = False
                style.scale_x = 80
                style.scale_y = 100
                style.spacing = 0
                style.angle = 0
                style.border_style = 1
                style.outline = 3
                style.shadow = 3
                style.alignment = 2
                style.margin_l = 60
                style.margin_r = 60
                style.margin_v = 50
                style.encoding = 1

            if style.name == "OS" and style.fontname == "Arial Unicode MS" and style.fontsize == 18:
                style.fontname = "UVN Sach Vo"
                style.fontsize = 81
                style.primary_color = ass.data.Color.from_ass("&H00FFFFFF")
                style.secondary_color = ass.data.Color.from_ass("&H00000000")
                style.outline_color = ass.data.Color.from_ass("&H4D000000")
                style.back_color = ass.data.Color.from_ass("&HBC000000")
                style.bold = True
                style.italic = False
                style.underline = False
                style.strike_out = False
                style.scale_x = 80
                style.scale_y = 100
                style.spacing = 0
                style.angle = 0
                style.border_style = 1
                style.outline = 3
                style.shadow = 3
                style.alignment = 8
                style.margin_l = 60
                style.margin_r = 60
                style.margin_v = 50
                style.encoding = 1

            if style.name == "Italics" and style.fontname == "Arial Unicode MS" and style.fontsize == 20:
                style.fontname = "UVN Sach Vo"
                style.fontsize = 81
                style.primary_color = ass.data.Color.from_ass("&H00FFFFFF")
                style.secondary_color = ass.data.Color.from_ass("&H00000000")
                style.outline_color = ass.data.Color.from_ass("&H4D000000")
                style.back_color = ass.data.Color.from_ass("&HBC000000")
                style.bold = True
                style.italic = True
                style.underline = False
                style.strike_out = False
                style.scale_x = 80
                style.scale_y = 100
                style.spacing = 0
                style.angle = 0
                style.border_style = 1
                style.outline = 3
                style.shadow = 3
                style.alignment = 2
                style.margin_l = 60
                style.margin_r = 60
                style.margin_v = 50
                style.encoding = 1

            if style.name == "On Top" and style.fontname == "Arial Unicode MS" and style.fontsize == 20:
                style.fontname = "UVN Sach Vo"
                style.fontsize = 81
                style.primary_color = ass.data.Color.from_ass("&H00FFFFFF")
                style.secondary_color = ass.data.Color.from_ass("&H00000000")
                style.outline_color = ass.data.Color.from_ass("&H4D000000")
                style.back_color = ass.data.Color.from_ass("&HBC000000")
                style.bold = True
                style.italic = False
                style.underline = False
                style.strike_out = False
                style.scale_x = 80
                style.scale_y = 100
                style.spacing = 0
                style.angle = 0
                style.border_style = 1
                style.outline = 3
                style.shadow = 3
                style.alignment = 8
                style.margin_l = 60
                style.margin_r = 60
                style.margin_v = 50
                style.encoding = 1

            if style.name == "DefaultLow" and style.fontname == "Arial Unicode MS" and style.fontsize == 20:
                style.fontname = "UVN Sach Vo"
                style.fontsize = 81
                style.primary_color = ass.data.Color.from_ass("&H00FFFFFF")
                style.secondary_color = ass.data.Color.from_ass("&H00000000")
                style.outline_color = ass.data.Color.from_ass("&H4D000000")
                style.back_color = ass.data.Color.from_ass("&HBC000000")
                style.bold = True
                style.italic = False
                style.underline = False
                style.strike_out = False
                style.scale_x = 80
                style.scale_y = 100
                style.spacing = 0
                style.angle = 0
                style.border_style = 1
                style.outline = 3
                style.shadow = 3
                style.alignment = 2
                style.margin_l = 60
                style.margin_r = 60
                style.margin_v = 50
                style.encoding = 1

            if style.fontname == "Noto Sans" and style.fontsize == 100:
                style.fontname = "UVN Sach Vo"
                style.fontsize = 81
                style.primary_color = ass.data.Color.from_ass("&H00FFFFFF")
                style.secondary_color = ass.data.Color.from_ass("&H00000000")
                style.outline_color = ass.data.Color.from_ass("&H4D000000")
                style.back_color = ass.data.Color.from_ass("&HBC000000")
                style.bold = True
                style.italic = False
                style.underline = False
                style.strike_out = False
                style.scale_x = 80
                style.scale_y = 100
                style.spacing = 0
                style.angle = 0
                style.border_style = 1
                style.outline = 3
                style.shadow = 3
                style.alignment = 2
                style.margin_l = 60
                style.margin_r = 60
                style.margin_v = 50
                style.encoding = 1


def clean_subtitle(input_file, output_file, is_replace_font=False):
    is_closedcaptionconverter = fix_closedcaptionconverter(input_file, input_file)
    with open(input_file, "r", encoding="utf-8-sig") as f:
        doc = ass.parse(f)
    remove_embedded_fonts(doc)
    remove_unused_styles(doc, is_replace_font, is_closedcaptionconverter)
    with open(output_file, "w", encoding="utf-8-sig") as f:
        doc.dump_file(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove unused styles from an .ass subtitle file or all .ass files in a directory."
    )

    parser.add_argument(
        "inputs",
        nargs="+",  # Accept one or more input paths
        help="Path(s) to input .ass file(s) or directories containing .ass files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        help="Path to the output .ass file or directory. Defaults to overwriting the input file(s).",
    )
    parser.add_argument(
        "-r",
        "--replace-font",
        dest="replace_font",
        action="store_true",
        help="Replace crunchyroll and bilibili fonts.",
    )

    args = parser.parse_args()
    replace_font = args.replace_font

    for input_path in args.inputs:
        if os.path.isdir(input_path):
            # Input is a directory: process all .ass files recursively
            for file_path in glob.glob(os.path.join(input_path, "**", "*.ass"), recursive=True):
                output_dir = args.output if args.output else os.path.dirname(file_path)
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.basename(file_path)
                output_path = os.path.join(output_dir, filename)
                clean_subtitle(file_path, output_path, is_replace_font=replace_font)
        elif os.path.isfile(input_path):
            # Input is a single file
            if args.output:
                # If multiple inputs but single output is provided, treat output as directory
                output_dir = args.output
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.basename(input_path)
                output_path = os.path.join(output_dir, filename)
            else:
                output_path = input_path
            clean_subtitle(input_path, output_path, is_replace_font=replace_font)
        else:
            print(f"Warning: {input_path} does not exist, skipping...")
