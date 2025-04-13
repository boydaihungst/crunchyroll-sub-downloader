#!/bin/bash

set -euo pipefail

cleanup() {
    [[ -f "${tmp_output_ass:-}" ]] && rm -f "$tmp_output_ass"
}
trap cleanup EXIT HUP INT QUIT ABRT TERM

is_subtitle() {
    local file="$1"
    [[ "${file##*.}" == "ass" ]]
}

modify_ass() {
    local input="$1"
    tmp_output_ass="$(mktemp)"

    cp "$input" "$tmp_output_ass"

    # Modify resolution and default style
    sed -i \
        -e 's/^PlayResX: 640/PlayResX: 1920/' \
        -e 's/^PlayResY: 360/PlayResY: 1080/' \
        -e 's/Arial Unicode MS,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H7F404040,-1,0,0,0,100,100,0,0,1,2,1,2,0020,0020,0022,0/UVN Sach Vo,81,\&H00FFFFFF,\&H000000FF,\&H4D000000,\&H81000000,-1,0,0,0,100,100,0,0,1,2,3,2,60,60,30,1/' \
        -e 's/Arial Unicode MS,18,&H00FFFFFF,&H0000FFFF,&H00000000,&H7F404040,-1,0,0,0,100,100,0,0,1,2,1,8,0001,0001,0015,0/UVN Sach Vo,81,\&H00FFFFFF,\&H000000FF,\&H4D000000,\&H81000000,-1,0,0,0,100,100,0,0,1,2,3,8,60,60,30,1/' \
        -e 's/Arial Unicode MS,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H7F404040,-1,-1,0,0,100,100,0,0,1,2,1,2,0020,0020,0022,0/UVN Sach Vo,81,\&H00FFFFFF,\&H000000FF,\&H4D000000,\&H81000000,-1,-1,0,0,100,100,0,0,1,2,3,8,60,60,30,1/' \
        -e 's/Arial Unicode MS,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H7F404040,-1,0,0,0,100,100,0,0,1,2,1,8,0020,0020,0022,0/UVN Sach Vo,81,\&H00FFFFFF,\&H000000FF,\&H4D000000,\&H81000000,-1,0,0,0,100,100,0,0,1,2,3,8,60,60,30,1/' \
        -e 's/Arial Unicode MS,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H7F404040,-1,0,0,0,100,100,0,0,1,2,1,2,0020,0020,0010,0/UVN Sach Vo,81,\&H00FFFFFF,\&H000000FF,\&H4D000000,\&H81000000,-1,0,0,0,100,100,0,0,1,2,3,2,60,60,30,1/' \
        "$tmp_output_ass"

    # Step 1: Extract used styles
    local used_styles
    used_styles=$(awk '
    BEGIN { FS="," }
    /^\[Events\]/ { in_events = 1; next }
    /^\[/ && $0 !~ /^\[Events\]/ { in_events = 0 }
    in_events && $1 ~ /^Dialogue:/ {
        style = $4
        gsub(/^ +| +$/, "", style)
        if (style != "") used[style] = 1
    }
    END {
        for (s in used) print s
    }
' "$tmp_output_ass")

    # Ensure Default is present
    if ! grep -qx "Default" <<<"$used_styles"; then
        used_styles="${used_styles}"$'\n'"Default"
    fi

    # Convert to array
    readarray -t used_array <<<"$used_styles"
    if [[ ${#used_array[@]} -eq 0 ]]; then
        echo "Error: No styles found." >&2
        cat "$tmp_output_ass"
        return 1
    fi

    # Build regex
    local pattern_elements=()
    for style in "${used_array[@]}"; do
        escaped_style=$(sed 's/[][\\.^$*+?(){}|]/\\&/g' <<<"$style")
        pattern_elements+=("^Style: ${escaped_style},")
    done
    local pattern
    pattern=$(
        IFS="|"
        echo "${pattern_elements[*]}"
    )

    # Filter Styles
    awk -v pat="$pattern" '
        BEGIN { in_styles = 0 }
        /^\[V4\+ Styles\]/ {
            in_styles = 1
            print
            next
        }
        /^\[/ && $0 !~ /^\[V4\+ Styles\]/ {
            if (in_styles == 1) print ""
            in_styles = 0
            print
            next
        }
        in_styles {
            if (/^Format:/ || /^;/ || ($0 ~ /^Style:/ && $0 ~ pat)) {
                print
            }
            next
        }
        { print }
        END {
            if (in_styles == 1) print ""
        }
    ' "$tmp_output_ass" >"${tmp_output_ass}.cleaned"

    mv "${tmp_output_ass}.cleaned" "$input"
}

# Entry point
input="$1"

if [[ -z "$input" ]]; then
    echo "Usage: $0 <file-or-folder>"
    exit 1
fi

if is_subtitle "$input" && [[ -f "$input" ]]; then
    modify_ass "$input"
elif [[ -d "$input" ]]; then
    find "$input" -type f -name "*.ass" -print0 | while IFS= read -r -d '' file; do
        modify_ass "$file"
    done
else
    echo "Error: '$input' is neither a valid subtitle file nor a directory."
    exit 2
fi
