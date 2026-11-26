import re
import codecs
from text_unidecode import unidecode

def DecodeFile(payment_file):
    with open(payment_file, "rb") as f:
        rawdata = f.read()

    # UTF-16 is only recognisable by its byte order mark
    if rawdata.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return rawdata.decode("utf-16")

    # Strict UTF-8 ("-sig" drops a leading BOM); Windows-1252 umlauts are never valid UTF-8, so those files fall through to cp1252
    try:
        return rawdata.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass

    return rawdata.decode("cp1252", errors="replace")

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

def NeedsReview(raw, cleaned):
    """Return True if SepaClean changed a name by more than the routine steps."""
    expected = re.sub(r"\s+", " ", NoUmlauts(raw)).strip()
    return cleaned != expected
