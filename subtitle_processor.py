import argparse
import glob
import os

import ass
import ass.data


def remove_unused_styles(input_file, output_file, is_replace_font=False):
    with open(input_file, "r", encoding="utf-8-sig") as f:
        doc = ass.parse(f)

    used_styles = set(event.style for event in doc.events if isinstance(event, ass.Dialogue))
    doc.styles = [style for style in doc.styles if style.name in used_styles]
    doc.info["PlayResX"] = "1920"
    doc.info["PlayResY"] = "1080"
    doc.info["ScaledBorderAndShadow"] = "Yes"
    if is_replace_font:
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
                style.margin_v = 40
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
                style.margin_v = 30
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
                style.margin_v = 30
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
                style.margin_v = 30
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
                style.margin_v = 30
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
                style.margin_v = 30
                style.encoding = 1
    with open(output_file, "w", encoding="utf-8-sig") as f:
        doc.dump_file(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove unused styles from an .ass subtitle file or all .ass files in a directory."
    )
    parser.add_argument("input", help="Path to the input .ass file or directory containing .ass files.")
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

    if os.path.isdir(args.input):
        input_dir = args.input

        for file_path in glob.glob(os.path.join(input_dir, "**", "*.ass"), recursive=True):
            output_dir = args.output if args.output else os.path.dirname(file_path)
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.basename(file_path)
            output_path = os.path.join(output_dir, filename)
            remove_unused_styles(file_path, output_path, is_replace_font=replace_font)
    else:
        input_path = args.input
        output_path = args.output if args.output else input_path
        remove_unused_styles(input_path, output_path, is_replace_font=replace_font)
