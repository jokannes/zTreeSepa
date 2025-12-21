# -*- coding: utf-8 -*-
"""
Created on Wed Jul 9 16:22:28 2025

zTree payment file to SEPA XML converter

@author: Johannes
"""


# Version info
version = "0.6.0"
version_date = "21 December 2025"
github_link = "https://github.com/jokannes/zTreeSepa"


# Packages
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import datetime, uuid
import webbrowser
from schwifty import IBAN
from sepaxml import SepaTransfer


# Import own functions
from utils import NoUmlauts, DecodeFile
from settings import LoadSettings
from pdf import MakePDF
from parse import ParseFile


# Get correct working directory
if getattr(sys, 'frozen', False):
    # Running as exe
    base_path = sys._MEIPASS
    app_path = os.path.dirname(sys.executable)
else:
    # Running as script
    app_path = os.path.dirname(os.path.abspath(__file__))


# Load settings (payer banking info is here)
settings_file = os.path.join(app_path, "settings.json")
settings = LoadSettings(settings_file)


# Function for reading a .pay file
def ImportFile(payer_name, payer_iban, payer_bic, currency, reference, reference_placeholder, experiment, experiment_placeholder):
    payer_name = NoUmlauts(payer_name.strip())
    payer_iban = payer_iban.strip().replace(" ", "")
    payer_bic = payer_bic.strip()
    currency = currency.strip().upper()
    reference = reference.get().strip()
    experiment = experiment.get().strip()

    if (not payer_name or not payer_iban or not currency or
        not reference or reference == reference_placeholder or
        not experiment or experiment == experiment_placeholder):
        messagebox.showwarning("Missing Info", "Please fill in all required fields, including Reference and Experiment Name.")
        return

    try:
        IBAN(payer_iban)
    except Exception:
        messagebox.showerror("Invalid IBAN", "Payer IBAN is not valid.")
        return

    file_path = filedialog.askopenfilename(filetypes=[("Import payment file", "*.pay")])
    if not file_path:
        return

    try:
        raw_file = DecodeFile(file_path)
        rows = ParseFile(raw_file)

        if not rows:
            messagebox.showwarning("No Valid Payments", "No valid payment entries were found.")
            return

        rows.sort(key=lambda r: r["name"].lower())
        FileView(rows, {
            "name": payer_name,
            "IBAN": payer_iban,
            "BIC": payer_bic,
            "batch": True,
            # "domestic": True, # This seems to be required in CH (but ZKB accepts it without?), not sure if adding this will break things in DE
            "currency": currency,
            "reference": reference,
            "experiment": experiment
        })
    except Exception as e:
        messagebox.showerror("Error", str(e))


# Set up the file viewer for after a .pay file has been opened
def FileView(data_rows, config):
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
        tree.heading(col, text = col)
        anchor = "e" if col == "Amount" else "w"
        width = 60 if col in ("Index", "Amount") else 180
        tree.column(col, width=width, anchor=anchor)

    for idx, row in enumerate(data_rows, 1):
        tree.insert("", "end", values=(idx, row["name"], row["iban"], row.get("bic", ""), f"{row['amount']:.2f}"))

    def profit_masschange():
        def apply_profit_masschange():
            try:
                delta = float(entry_amount_change.get().strip().replace(",", "."))
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number.")
                return

            for row in data_rows:
                row["amount"] += delta

            for item in tree.get_children():
                tree.delete(item)
            for idx, row in enumerate(data_rows, 1):
                tree.insert("", "end", values=(idx, row["name"], row["iban"], row["bic"], f"{row['amount']:.2f}"))

            add_window.destroy()

        add_window = tk.Toplevel(preview_window)
        add_window.title("Add amount to all payoffs")
        tk.Label(add_window, text = "Enter amount to add (e.g., 5 or -3):").grid(row=0, column=0, padx=10, pady=10)
        entry_amount_change = tk.Entry(add_window, width=10, justify="left")
        entry_amount_change.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(add_window, text = "Apply", command=apply_profit_masschange).grid(row=1, column=0, columnspan=2, pady=10)

    def add_surplus_participant():
        def save_surplus_participant():
            name = NoUmlauts(surplus_name.get().strip())
            iban_raw = surplus_iban.get().strip().replace(" ", "").upper()
            amount_str = surplus_amount.get().strip()

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
        
        tk.Label(add_window, text = "Name:").grid(row=0, column=0, sticky="e")
        tk.Label(add_window, text = "IBAN:").grid(row=1, column=0, sticky="e")
        tk.Label(add_window, text = "Amount:").grid(row=2, column=0, sticky="e")

        surplus_name = tk.Entry(add_window, width=40)
        surplus_iban = tk.Entry(add_window, width=40)
        surplus_amount = tk.Entry(add_window, width=40, justify="left")
        
        name_placeholder = tk.Label(add_window, text = "Format: Firstname Lastname", fg="gray", anchor="w", justify="left")
        amount_placeholder = tk.Label(add_window, text = "Format: 7", fg="gray", anchor="w", justify="left")

        surplus_name.grid(row=0, column=1, padx=10, pady=5)
        surplus_iban.grid(row=1, column=1, padx=10, pady=5)
        surplus_amount.grid(row=2, column=1, padx=10, pady=5)
        
        name_placeholder.grid(row=0, column=2, sticky="w", padx=(5,10))
        amount_placeholder.grid(row=2, column=2, sticky="w", padx=(5,10))        

        tk.Button(add_window, text = "Add", command = save_surplus_participant).grid(row=3, column=0, columnspan=2, pady=10)

    def confirm_and_generate():
        try:
            sepa = SepaTransfer(config, schema = schema, clean=True)
            for idx, row in enumerate(data_rows, 1):
                try:
                    payment = {
                        "name": row["name"][:70],
                        "IBAN": row["iban"],
                        "BIC": row.get("bic") or "",
                        "amount": int(round(row["amount"] * 100)),
                        "execution_date": datetime.date.today() + datetime.timedelta(days=2),
                        "description": config["reference"][:140],
                        "endtoend_id": str(uuid.uuid1()).replace("-", ""),
                    }
                    sepa.add_payment(payment)
                except Exception as e:
                    raise Exception(f"Error in row {idx} ({row['name']} - {row['iban']}): {e}")
    
            # Build safe default filename
            experiment_raw = NoUmlauts(config["experiment"])
            reference_raw = NoUmlauts(config["reference"])
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
                MakePDF(pdf_path, config.get("experiment"), data_rows, config.get("currency"), config.get("reference"))
    
                preview_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    btn_frame = tk.Frame(preview_window)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text = "Add amount to all payoffs", command = profit_masschange).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text = "Add surplus participant", command = add_surplus_participant).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text = "Generate output files", command = confirm_and_generate).grid(row=0, column=2, padx=10)
    tk.Button(btn_frame, text = "Cancel", command = preview_window.destroy).grid(row=0, column=3, padx=10)


# Make GUI resolution adaptive to screen resolution
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


# Initialise GUI
root = tk.Tk()


# GUI settings 
screen_w = int(root.winfo_screenwidth())
screen_h = int(root.winfo_screenheight())
root.minsize(800, 400)
root.maxsize(screen_w, screen_h)
root.title("zTreeSepa")


# Add top menu bar
menubar = tk.Menu(root)


# Add file menu
file_menu = tk.Menu(menubar, tearoff = 0)
file_menu.add_command(label = "Import payment file", command = lambda: ImportFile(payer_name, payer_iban, payer_bic, currency, reference, reference_placeholder, experiment, experiment_placeholder))
file_menu.add_separator()
file_menu.add_command(label = "Quit", command = root.quit)
menubar.add_cascade(label = "File", menu = file_menu)


# Add help menu
help_menu = tk.Menu(menubar, tearoff = 0)
help_menu.add_command(label="Open GitHub", command = lambda: webbrowser.open(github_link))
help_menu.add_command(label = "About", command = lambda: tk.messagebox.showinfo("About", f"zTreeSepa\n\nVersion {version}\nVersion date: {version_date}"))
menubar.add_cascade(label = "Help", menu = help_menu)

root.config(menu=menubar)

# Use zTreeSepa icon for the window when running as .exe
if getattr(sys, 'frozen', False):
    try:
        root.iconbitmap(sys.executable)
    except Exception:
        pass

# Set up frame with payer infos
frame_settings = tk.LabelFrame(root, text = "Payer Banking Info", padx=10, pady=10)
frame_settings.pack(fill="x", padx=20, pady=10)

info_label = tk.Label(root, text = "Payer details are read-only.\nTo change, edit settings.json manually.", fg="gray", justify="left")
info_label.pack(pady=(0, 10), padx=20, anchor="w")

payer_name = settings.get("payer_name", "")
payer_iban = settings.get("payer_iban", "")
payer_bic = settings.get("payer_bic", "")
currency = settings.get("currency", "EUR")
schema = settings.get("default_schema", "")
                    
payer_name_label = tk.Label(frame_settings, text = payer_name, width=60, anchor="w")
payer_iban_label = tk.Label(frame_settings, text = payer_iban, width=60, anchor="w")
payer_bic_label = tk.Label(frame_settings, text = payer_bic, width=60, anchor="w")
currency_label = tk.Label(frame_settings, text = currency, width=60, anchor="w")

reference = tk.Entry(frame_settings, width=70, justify="left")
experiment = tk.Entry(frame_settings, width=70, justify="left")

widgets = [
    ("Payer Name:", payer_name_label),
    ("Payer IBAN:", payer_iban_label),
    ("Payer BIC:", payer_bic_label),
    ("Currency:", currency_label),
    ("Payment Reference:", reference),
    ("Experiment Name:", experiment),
]

for i, (label, widget) in enumerate(widgets):
    tk.Label(frame_settings, text = label).grid(row=i, column=0, sticky="e")
    widget.grid(row=i, column=1, padx=(10,0), pady=5, sticky="w")

# Placeholder setup
reference_placeholder = settings.get("placeholder_reference", "e.g. Payment Round 3")
experiment_placeholder = settings.get("placeholder_experiment", "e.g. Study A - Session 1")

reference_placeholder_label = tk.Label(frame_settings, text = reference_placeholder, fg="gray", anchor="w", justify="left")
reference_placeholder_label.grid(row=4, column=2, sticky="w", padx=(1,10))

experiment_placeholder_label = tk.Label(frame_settings, text = experiment_placeholder, fg="gray", anchor="w", justify="left")
experiment_placeholder_label.grid(row=5, column=2, sticky="w", padx=(1,10))

# Add button to import .pay file
tk.Button(root, text = "Payment file", command = lambda: ImportFile(payer_name, payer_iban, payer_bic, currency, reference, reference_placeholder, experiment, experiment_placeholder), height=2, width=25).pack(pady=20)

root.mainloop()