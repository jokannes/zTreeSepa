import chardet

def DecodeFile(payment_file):
    with open(payment_file, "rb") as f:
        rawdata = f.read()

    result = chardet.detect(rawdata)
    encoding = result["encoding"]
    
    try:
        text = rawdata.decode(encoding)
    except Exception as e:
        print(f"Decoding failed ({encoding}): {e}.")
    return text

def NoUmlauts(text):
    return (
        text.replace("ä", "ae").replace("Ä", "Ae")
            .replace("ö", "oe").replace("Ö", "Oe")
            .replace("ü", "ue").replace("Ü", "Ue")
            .replace("ß", "ss")
    )