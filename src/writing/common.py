def write_text_to_file(text: str, file_path: str):
    """
    Write text to a file.

    :param text: the text to write (str)
    :param file_path: the path of the file to write to (str)
    :return: None
    """
    file = open(file_path, "w")
    file.write(text)
    file.close()
