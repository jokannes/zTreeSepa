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

# For PDF output
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

if getattr(sys, 'frozen', False):
    # Running as exe
    base_path = sys._MEIPASS
    app_path = os.path.dirname(sys.executable)
else:
    # Running as script
    app_path = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(app_path, "settings.json")
def load_settings():
    default_settings = {
        "company_name": "My Company GmbH",
        "company_iban": "DE02100100109307118603",
        "company_bic": "PBNKDEFFXXX",
        "currency": "EUR",
        "placeholder_reference": "e.g., Lab Payment 10 July 2025 - 10am",
        "placeholder_experiment": "e.g., Study A - Session 1",
        "default_amount": 5.00
    }

    if not os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8-sig") as f:
                json.dump(default_settings, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create default settings.json: {e}")
            return default_settings

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load settings.json: {e}")
        return default_settings

def normalize_umlauts(text):
    return (
        text.replace("ä", "ae").replace("Ä", "Ae")
            .replace("ö", "oe").replace("Ö", "Oe")
            .replace("ü", "ue").replace("Ü", "Ue")
            .replace("ß", "ss")
    )

def add_placeholder(entry, placeholder):
    entry.insert(0, placeholder)
    entry.config(fg="gray")

    def on_focus_in(event):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg="gray")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

def select_file():
    company_name = entry_name.get().strip()
    company_iban_raw = entry_iban.get().strip().replace(" ", "")
    company_bic = entry_bic.get().strip()
    currency = entry_currency.get().strip().upper()
    reference = entry_reference.get().strip()
    experiment = entry_experiment.get().strip()

    if (not company_name or not company_iban_raw or not currency or
        not reference or reference == reference_placeholder or
        not experiment or experiment == experiment_placeholder):
        messagebox.showwarning("Missing Info", "Please fill in all required fields, including Reference and Experiment Name.")
        return

    try:
        IBAN(company_iban_raw)
    except Exception:
        messagebox.showerror("Invalid IBAN", "Company IBAN is not valid.")
        return

    file_path = filedialog.askopenfilename(filetypes=[("Import payment file", "*.pay")])
    if file_path:
        try:
            generate_sepa_preview(file_path, {
                "name": company_name,
                "IBAN": company_iban_raw,
                "BIC": company_bic,
                "batch": True,
                "currency": currency,
                "reference": reference,
                "experiment": experiment
            }, use_bic_lookup=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

def generate_payment_pdf(file_path, experiment_name, payments, currency, reference):
    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph(f"<b>Experiment: {experiment_name}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table data: header + rows
    data = [["Index", "Name", "IBAN", "Amount", "Currency", "Reference"]]
    total_sum = 0

    for idx, payment in enumerate(payments, 1):
        data.append([
            str(idx),
            payment["name"],
            payment["iban"],
            f"{payment['amount']:.2f}",
            currency,
            reference
        ])
        total_sum += payment['amount']

    # Table style
    table = Table(data, repeatRows=1, hAlign='LEFT')
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ])
    table.setStyle(table_style)

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Total sum
    total_amount = sum(p["amount"] for p in payments)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Gesamtsumme:</b> {total_amount:.2f} {currency}", styles['Normal']))
    
    # Signature line
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Unterschrift Experimentator: ____________________________", styles['Normal']))
    
    # Timestamp
    timestamp = datetime.datetime.now().strftime("Datei erstellt am %d.%m.%Y um %H:%M Uhr")
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<i>{timestamp}</i>", styles['Normal']))

    # Build PDF
    doc.build(elements)

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
        columns=("Index", "Name", "IBAN", "BIC", "Amount"),
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
    for col in ("Index", "Name", "IBAN", "BIC", "Amount"):
        tree.heading(col, text=col)
        anchor = "e" if col == "Amount" else "w"
        width = 60 if col in ("Index", "Amount") else 180
        tree.column(col, width=width, anchor=anchor)

    for idx, row in enumerate(data_rows, 1):
        tree.insert("", "end", values=(idx, row["name"], row["iban"], row.get("bic", ""), f"{row['amount']:.2f}"))

    def add_row():
        def save_row():
            name = normalize_umlauts(entry_row_name.get().strip())
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
            data_rows.sort(key=lambda r: r["name"].lower())
            
            # Clear and re-insert all rows with index
            for row in tree.get_children():
                tree.delete(row)
            
            for idx, row in enumerate(data_rows, 1):
                tree.insert("", "end", values=(idx, row["name"], row["iban"], row["bic"], f"{row['amount']:.2f}"))
            
            add_window.destroy()

        add_window = tk.Toplevel(preview_window)
        add_window.title("Add Surplus Participant")
        tk.Label(add_window, text="Name:").grid(row=0, column=0, sticky="e")
        tk.Label(add_window, text="IBAN:").grid(row=1, column=0, sticky="e")
        tk.Label(add_window, text="Amount:").grid(row=2, column=0, sticky="e")

        entry_row_name = tk.Entry(add_window, width=40)
        entry_row_iban = tk.Entry(add_window, width=40)
        entry_row_amount = tk.Entry(add_window, width=20, justify="left")
        
        add_placeholder(entry_row_name, "e.g., Lastname, Firstname")
        add_placeholder(entry_row_amount, "e.g., 7")

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
    
            # Build safe default filename
            experiment_raw = normalize_umlauts(config["experiment"])
            reference_raw = normalize_umlauts(config["reference"])
            safe_experiment = experiment_raw.replace(" ", "_").replace(".", "").replace(":", "")
            safe_reference = reference_raw.replace(" ", "_").replace(".", "").replace(":", "")
            default_filename = f"{safe_experiment}_{safe_reference}.xml"
            
            # Show dialog with prefilled name
            output_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XML files", "*.xml")],
                initialfile=default_filename
            )

            if output_path:
                with open(output_path, "wb") as out:
                    out.write(sepa.export())
                messagebox.showinfo("Success", "Output files generated.")
    
                # Generate PDF next to XML with same base name
                pdf_path = os.path.splitext(output_path)[0] + ".pdf"
                generate_payment_pdf(pdf_path, config.get("experiment"), data_rows, config.get("currency"), config.get("reference"))
    
                preview_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    btn_frame = tk.Frame(preview_window)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Add Surplus Participant", command=add_row).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="Generate SEPA XML", command=confirm_and_generate).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="Cancel", command=preview_window.destroy).grid(row=0, column=2, padx=10)

def generate_sepa_preview(payment_file, config, use_bic_lookup):
    rows = []
    with open(payment_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            first = row.get('firstName', '').strip()
            last = row.get('lastName', '').strip()
            name = normalize_umlauts(f"{first} {last}".strip())
        
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

    rows.sort(key=lambda r: r["name"].lower())
    preview_and_confirm(rows, config)

# --- GUI Setup ---

root = tk.Tk()
root.title("zTreeSepa")
root.geometry("600x480")

settings = load_settings()

reference_placeholder = settings.get("placeholder_reference", "")
experiment_placeholder = settings.get("placeholder_experiment", "")

frame_settings = tk.LabelFrame(root, text="Company Banking Info", padx=10, pady=10)
frame_settings.pack(fill="x", padx=20, pady=10)

info_label = tk.Label(root, text="Company details are read-only.\nTo change, edit settings.json manually.", fg="gray", justify="left")
info_label.pack(pady=(0, 10), padx=20, anchor="w")

entry_name = tk.Entry(frame_settings, width=40, justify="left")
entry_iban = tk.Entry(frame_settings, width=40, justify="left")
entry_bic = tk.Entry(frame_settings, width=20, justify="left")
entry_currency = tk.Entry(frame_settings, width=10, justify="left")
entry_reference = tk.Entry(frame_settings, width=40, justify="left")
entry_experiment = tk.Entry(frame_settings, width=40, justify="left")

widgets = [
    ("Company Name:", entry_name),
    ("Company IBAN:", entry_iban),
    ("Company BIC:", entry_bic),
    ("Currency (e.g., EUR):", entry_currency),
    ("Payment Reference:", entry_reference),
    ("Experiment Name:", entry_experiment),
]

for i, (label, widget) in enumerate(widgets):
    tk.Label(frame_settings, text=label).grid(row=i, column=0, sticky="e")
    widget.grid(row=i, column=1, padx=10, pady=5, sticky="w")

entry_name.insert(0, settings.get("company_name", ""))
entry_iban.insert(0, settings.get("company_iban", ""))
entry_bic.insert(0, settings.get("company_bic", ""))
entry_currency.insert(0, settings.get("currency", "EUR"))

# Make these read-only
entry_name.config(state="readonly")
entry_iban.config(state="readonly")
entry_bic.config(state="readonly")
entry_currency.config(state="readonly")

# Placeholder setup
reference_placeholder = settings.get("placeholder_reference", "e.g. Payment Round 3")
experiment_placeholder = settings.get("placeholder_experiment", "e.g. Study A - Session 1")

entry_reference.delete(0, tk.END)
entry_experiment.delete(0, tk.END)

add_placeholder(entry_reference, reference_placeholder)
add_placeholder(entry_experiment, experiment_placeholder)

tk.Button(root, text="Import payment file", command=select_file, height=2, width=25).pack(pady=20)

root.mainloop()
