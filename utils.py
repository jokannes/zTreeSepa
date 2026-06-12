import chardet

def DecodeFile(payment_file):
    with open(payment_file, "rb") as f:
        rawdata = f.read()

    result = chardet.detect(rawdata)
    encoding = result["encoding"] or "utf-8"

    try:
        return rawdata.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        # latin-1 maps every byte, so this cannot fail; rows that were
        # garbled by the wrong encoding are caught by the IBAN validation
        return rawdata.decode("latin-1")

def NoUmlauts(text):
    return (
        text.replace("ä", "ae").replace("Ä", "Ae")
            .replace("ö", "oe").replace("Ö", "Oe")
            .replace("ü", "ue").replace("Ü", "Ue")
            .replace("ß", "ss")
    )