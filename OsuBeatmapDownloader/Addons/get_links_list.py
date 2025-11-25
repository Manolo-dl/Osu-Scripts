from re import compile

def get_links_list(file, regex):
    regex_tool = compile(regex)  # <- https://osu\.ppy\.sh/beatmapsets/\d+#(osu|mania|fruits|taiko)/\d+

    with open(file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if regex_tool.fullmatch(line.strip())]
