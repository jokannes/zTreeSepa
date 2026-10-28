import re
import chardet
from text_unidecode import unidecode

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

# The characters the SEPA (EPC) standard permits in free-text fields such as
# names and remittance/reference info:
#     a-z  A-Z  0-9  and  / - ? : ( ) . , ' +  and space
# Anything outside this may be rejected or silently altered by the receiving
# bank, so every value that ends up in the SEPA XML is run through SepaClean.
_SEPA_ALLOWED = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "/-?:().,'+ "
)

def SepaClean(text):
    """Make arbitrary user text safe for SEPA transfer fields.

    German umlauts are spelled out (ae/oe/ue/ss) for readability; any other
    non-ASCII (French/Nordic/Polish/... accents, currency signs, typographic
    punctuation) is transliterated to ASCII via unidecode; '&' becomes '+';
    and every remaining character outside the SEPA-permitted set is replaced
    with a space. Runs of whitespace are then collapsed and the ends stripped.
    """
    text = unidecode(NoUmlauts(text))
    text = text.replace("&", "+")
    text = "".join(c if c in _SEPA_ALLOWED else " " for c in text)
    return re.sub(r"\s+", " ", text).strip()
