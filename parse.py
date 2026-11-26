import csv
import io
from decimal import Decimal, ROUND_HALF_UP
from utils import SepaClean, NeedsReview
from schwifty import IBAN
from tkinter import messagebox

def ParseFile(file_content):
    valid_rows = []
    discarded_rows = []
    review_rows = []
    f = io.StringIO(file_content)
    reader = csv.DictReader(f, delimiter='\t')
    if reader.fieldnames is None:
        raise ValueError("The payment file is empty.")
    old_format = 'adress' not in reader.fieldnames

    for row in reader:
        name = None
        iban_raw = None
        try:
            
            # Different logic for older ztree versions with differently structured payment file
            if old_format:
                
                # Skip rows that don't contain payee info (in files from zTree versions <6 it might otherwise try to strip other rows that are NoneType)
                if not row.get('Name') or not row.get('Profit') or not row.get('Computer'):
                    continue
                name_iban, raw_name = row['Name'].split(',', 1)
                name = SepaClean(raw_name)
                iban_raw = name_iban.strip().replace(" ", "")
                amount = Decimal(row['Profit'].strip().replace(',', '.'))
            
            # Logic for zTree versions 5 and above (combo-pay file)
            else:
                
                # Skip rows that don't contain payee info (in files from zTree versions <6 it might otherwise try to strip other rows that are NoneType)
                if not row.get('adress') or not row.get('Payment'):
                    continue
                first = row.get('firstName', '').strip()
                last = row.get('lastName', '').strip()
                raw_name = f"{first} {last}"
                name = SepaClean(raw_name)
                iban_raw = row.get('adress', '').strip().replace(" ", "").upper()
                amount = Decimal(row['Payment'].strip().replace(',', '.'))

            amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            iban_obj = IBAN(iban_raw)
            valid_rows.append({"name": name, "iban": str(iban_obj), "amount": amount, "bic": getattr(iban_obj, "bic", None)})
            if NeedsReview(raw_name, name):
                review_rows.append({"raw": raw_name.strip(), "name": name})
        except Exception:
            # name/iban_raw may not have been set yet when the error occurred -
            # fall back to the raw fields so the warning still identifies the row
            if name is None:
                name = (row.get('Name')
                        or f"{row.get('firstName') or ''} {row.get('lastName') or ''}".strip()
                        or "<unknown>")
            discarded_rows.append({"name": name, "iban": iban_raw or "<unknown>"})

    if discarded_rows:
        discard_info = "\n".join(f"{r['name']} | IBAN: {r['iban']}" for r in discarded_rows)
        messagebox.showwarning(
            "Invalid or Skipped Rows",
            f"{len(discarded_rows)} rows were discarded due to invalid IBANs or parsing errors:\n\n{discard_info}"
        )

    if review_rows:
        review_info = "\n".join(f"{r['raw']}  ->  {r['name']}" for r in review_rows)
        messagebox.showwarning(
            "Please Check Names",
            f"{len(review_rows)} names had to be changed because they contain characters "
            "not compatible with SEPA. Check payment file entries before "
            "transferring to the bank and change manually if needed"
            f":\n\n{review_info}"
        )
    
    return valid_rows