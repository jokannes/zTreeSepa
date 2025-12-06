import csv
import io
from utils import NoUmlauts
from schwifty import IBAN
from tkinter import messagebox

def ParseFile(file_content):
    valid_rows = []
    discarded_rows = []
    f = io.StringIO(file_content)
    reader = csv.DictReader(f, delimiter='\t')
    old_format = 'adress' not in reader.fieldnames

    for row in reader:
        try:
            
            # Different logic for older ztree versions with differently structured payment file
            if old_format:
                
                # Skip rows that don't contain payee info (in files from zTree versions <6 it might otherwise try to strip other rows that are NoneType)
                if not row.get('Name') or not row.get('Profit') or not row.get('Computer'):
                    continue
                name_iban, name = [NoUmlauts(part.strip()) for part in row['Name'].split(',', 1)]
                iban_raw = name_iban.replace(" ", "")
                amount = float(row['Profit'].strip().replace(',', '.'))
            
            # Logic for zTree versions 5 and above (combo-pay file)
            else:
                
                # Skip rows that don't contain payee info (in files from zTree versions <6 it might otherwise try to strip other rows that are NoneType)
                if not row.get('adress') or not row.get('Payment'):
                    continue
                first = row.get('firstName', '').strip()
                last = row.get('lastName', '').strip()
                name = NoUmlauts(f"{first} {last}".strip())
                iban_raw = row.get('adress', '').strip().replace(" ", "").upper()
                amount = float(row['Payment'].strip().replace(',', '.'))

            iban_obj = IBAN(iban_raw)
            valid_rows.append({"name": name, "iban": str(iban_obj), "amount": amount, "bic": getattr(iban_obj, "bic", None)})
        except Exception:
            discarded_rows.append({"name": name, "iban": iban_raw})
    
    if discarded_rows:
        discard_info = "\n".join(f"{r.get('name')} | IBAN: {r.get('iban_raw')}" for r in discarded_rows)
        messagebox.showwarning(
            "Invalid or Skipped Rows",
            f"{len(discarded_rows)} rows were discarded due to invalid IBANs or parsing errors:\n\n{discard_info}"
        )
    
    return valid_rows