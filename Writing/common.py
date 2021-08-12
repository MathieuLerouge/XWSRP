def write_text_to_file(text: str, filename: str):
    file = open(filename, "w")
    file.write(text)
    file.close()
