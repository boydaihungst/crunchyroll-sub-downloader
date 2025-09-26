import argparse
import glob
import os

import ass
import ass.data


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


def remove_unused_styles(doc: ass.Document, is_replace_font=False):
    used_styles = set(event.style for event in doc.events if isinstance(event, ass.Dialogue))
    doc.styles = [style for style in doc.styles if style.name in used_styles]
    if is_replace_font:
        doc.info["PlayResX"] = "1920"
        doc.info["PlayResY"] = "1080"
        doc.info["ScaledBorderAndShadow"] = "Yes"
        for style in doc.styles:
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
    with open(input_file, "r", encoding="utf-8-sig") as f:
        doc = ass.parse(f)
    remove_embedded_fonts(doc)
    remove_unused_styles(doc, is_replace_font)
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
