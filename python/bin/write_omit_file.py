
def clean_string(text):
    text = text.strip()
    text = text.lower()
    text = "".join(t for t in text if t.isalnum())
    return text


def read_txt(path):
    input_lines = []
    with open(path, 'r') as notesfile:
        for line in notesfile:
            if "#" in line:
                line = line.split("#")
                del line[-1]
                line = line[0]
            line = clean_string(line)
            if not line == '':
                input_lines.append("".join([line, "\n"]))
    return input_lines


def write_txt(path, lines):
    with open(path, 'w') as output:
        output.writelines(lines)


if __name__ == "__main__":
    input = "planetnotes.txt"
    output = "skip_planets.txt"
    lines = read_txt(input)
    write_txt(output, lines)
