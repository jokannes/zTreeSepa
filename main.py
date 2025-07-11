# -*- coding: utf-8 -*-
"""
Created on Wed Jul  9 16:22:28 2025

zTree payment file to SEPA XML converter

@author: Johannes
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import json
import os
import sys
import datetime
from schwifty import IBAN
from sepaxml import SepaTransfer

if getattr(sys, 'frozen', False):
    # Running as exe
    base_path = sys._MEIPASS
    app_path = os.path.dirname(sys.executable)
else:
    # Running as script
    app_path = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(app_path, "settings.json")
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save settings: {e}")

def select_file():
    company_name = entry_name.get().strip()
    company_iban_raw = entry_iban.get().strip().replace(" ", "")
    company_bic = entry_bic.get().strip()
    currency = entry_currency.get().strip().upper()
    reference = entry_reference.get().strip()

    if not company_name or not company_iban_raw or not currency or not reference:
        messagebox.showwarning("Missing Info", "Please fill in all required fields.")
        return

    try:
        IBAN(company_iban_raw)
    except Exception:
        messagebox.showerror("Invalid IBAN", "Company IBAN is not valid.")
        return

    save_settings({
        "company_name": company_name,
        "company_iban": company_iban_raw,
        "company_bic": company_bic,
        "currency": currency,
        "reference": reference
    })

    file_path = filedialog.askopenfilename(filetypes=[("Import payment file", "*.pay")])
    if file_path:
        try:
            generate_sepa_preview(file_path, {
                "name": company_name,
                "IBAN": company_iban_raw,
                "BIC": company_bic,
                "batch": True,
                "currency": currency,
                "reference": reference
            }, use_bic_lookup=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

def preview_and_confirm(data_rows, config):
    preview_window = tk.Toplevel(root)
    preview_window.title("Payment Preview")
    preview_window.geometry("800x400")

    tree_frame = tk.Frame(preview_window)
    tree_frame.pack(fill="both", expand=True, pady=10)
    
    # Scrollbars
    tree_scroll_y = tk.Scrollbar(tree_frame, orient="vertical")
    tree_scroll_x = tk.Scrollbar(tree_frame, orient="horizontal")
    
    # Treeview widget
    tree = ttk.Treeview(
        tree_frame,
        columns=("Name", "IBAN", "BIC", "Amount"),
        show="headings",
        yscrollcommand=tree_scroll_y.set,
        xscrollcommand=tree_scroll_x.set
    )
    
    # Configure scrollbars
    tree_scroll_y.config(command=tree.yview)
    tree_scroll_x.config(command=tree.xview)
    
    tree_scroll_y.pack(side="right", fill="y")
    tree_scroll_x.pack(side="bottom", fill="x")
    tree.pack(side="left", fill="both", expand=True)
    
    # Column headings and widths
    for col in ("Name", "IBAN", "BIC", "Amount"):
        tree.heading(col, text=col)
        tree.column(col, width=180, anchor="w")


    for row in data_rows:
        tree.insert("", "end", values=(row["name"], row["iban"], row.get("bic", ""), f"{row['amount']:.2f}"))

    def add_row():
        def save_row():
            name = entry_row_name.get().strip()
            iban_raw = entry_row_iban.get().strip().replace(" ", "")
            amount_str = entry_row_amount.get().strip()

            if not name or not iban_raw or not amount_str:
                messagebox.showwarning("Missing Info", "Please complete all fields.")
                return

            try:
                IBAN(iban_raw)
                amount = float(amount_str.replace(',', '.'))
            except Exception:
                messagebox.showwarning("Invalid Input", "Check IBAN and amount format.")
                return

            bic = IBAN(iban_raw).bic
            data_rows.append({"name": name, "iban": iban_raw, "bic": bic, "amount": amount})
            tree.insert("", "end", values=(name, iban_raw, bic, f"{amount:.2f}"))
            add_window.destroy()

        add_window = tk.Toplevel(preview_window)
        add_window.title("Add Payment Row")
        tk.Label(add_window, text="Name:").grid(row=0, column=0, sticky="e")
        tk.Label(add_window, text="IBAN:").grid(row=1, column=0, sticky="e")
        tk.Label(add_window, text="Amount:").grid(row=2, column=0, sticky="e")

        entry_row_name = tk.Entry(add_window, width=40)
        entry_row_iban = tk.Entry(add_window, width=40)
        entry_row_amount = tk.Entry(add_window, width=20)

        entry_row_name.grid(row=0, column=1, padx=10, pady=5)
        entry_row_iban.grid(row=1, column=1, padx=10, pady=5)
        entry_row_amount.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(add_window, text="Add", command=save_row).grid(row=3, column=0, columnspan=2, pady=10)

    def confirm_and_generate():
        try:
            sepa = SepaTransfer(config, clean=True)
            for idx, row in enumerate(data_rows, 1):
                try:
                    payment = {
                        "name": row["name"][:70],
                        "IBAN": row["iban"],
                        "BIC": row.get("bic") or "",
                        "amount": int(round(row["amount"] * 100)),
                        "execution_date": datetime.date.today() + datetime.timedelta(days=2),
                        "description": config["reference"][:140],
                    }
                    sepa.add_payment(payment)
                except Exception as e:
                    raise Exception(f"Error in row {idx} ({row['name']} - {row['iban']}): {e}")

            output_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
            if output_path:
                with open(output_path, "wb") as out:
                    out.write(sepa.export())
                messagebox.showinfo("Success", "SEPA XML file generated.")
                preview_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    btn_frame = tk.Frame(preview_window)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Add Payment Row", command=add_row).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="Generate SEPA XML", command=confirm_and_generate).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="Cancel", command=preview_window.destroy).grid(row=0, column=2, padx=10)

def generate_sepa_preview(payment_file, config, use_bic_lookup):
    rows = []
    with open(payment_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            name = row.get('Name', '').strip()
            iban_raw = row.get('adress', '').strip().replace(" ", "")
            amount_str = row.get('Payment', '').strip()

            if not name or not iban_raw or not amount_str:
                continue

            try:
                iban_obj = IBAN(iban_raw)
                amount = float(amount_str.replace(',', '.'))
            except Exception:
                continue

            row_data = {
                "name": name,
                "iban": iban_raw,
                "amount": amount,
            }

            try:
                row_data["bic"] = iban_obj.bic
            except Exception:
                row_data["bic"] = None

            rows.append(row_data)

    if not rows:
        messagebox.showwarning("No Valid Payments", "No valid payment entries were found.")
        return

    preview_and_confirm(rows, config)

# --- GUI Setup ---
root = tk.Tk()
root.title("SEPA XML Generator")
root.geometry("600x480")

settings = load_settings()

frame_settings = tk.LabelFrame(root, text="Company Banking Info", padx=10, pady=10)
frame_settings.pack(fill="x", padx=20, pady=10)

entry_name = tk.Entry(frame_settings, width=40, justify="left")
entry_iban = tk.Entry(frame_settings, width=40, justify="left")
entry_bic = tk.Entry(frame_settings, width=20, justify="left")
entry_currency = tk.Entry(frame_settings, width=10, justify="left")
entry_reference = tk.Entry(frame_settings, width=40, justify="left")

widgets = [
    ("Company Name:", entry_name),
    ("Company IBAN:", entry_iban),
    ("Company BIC:", entry_bic),
    ("Currency (e.g., EUR):", entry_currency),
    ("Payment Reference:", entry_reference)
]

for i, (label, widget) in enumerate(widgets):
    tk.Label(frame_settings, text=label).grid(row=i, column=0, sticky="e")
    widget.grid(row=i, column=1, padx=10, pady=5, sticky="w")

entry_name.insert(0, settings.get("company_name", ""))
entry_iban.insert(0, settings.get("company_iban", ""))
entry_bic.insert(0, settings.get("company_bic", ""))
entry_currency.insert(0, settings.get("currency", "EUR"))
entry_reference.insert(0, settings.get("reference", ""))

tk.Button(root, text="Import payment file", command=select_file, height=2, width=25).pack(pady=20)

root.mainloop()
