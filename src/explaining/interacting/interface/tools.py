# Third-party library
from dash import html

# Local library
from src.utils.constants import LINE_BREAK_STRING


# Global functions
def convert_from_string_to_html(text: str):
    paragraphs = text.split(LINE_BREAK_STRING)
    html_text = []
    for paragraph in paragraphs[:-1]:
        html_text.append(paragraph)
        html_text.append(html.Br())
    html_text.append(paragraphs[-1])
    return html_text
