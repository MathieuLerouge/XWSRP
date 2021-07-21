def printTitleFrame(title):

    symbol = "#"
    spaces = "  "
    nbSymbols = len(title) + 2*len(spaces) + 2

    print(symbol*nbSymbols)
    print(symbol + spaces + title + spaces + symbol)
    print(symbol*nbSymbols)
