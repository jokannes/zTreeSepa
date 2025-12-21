import os
import json
from tkinter import messagebox

def LoadSettings(SETTINGS_FILE):
    default_settings = {
        "payer_name": "My Company GmbH",
        "payer_iban": "DE02100100109307118603",
        "payer_bic": "PBNKDEFFXXX",
        "currency": "EUR",
        "placeholder_reference": "e.g., Lab Payment 10 July 2025 - 10am",
        "placeholder_experiment": "e.g., Study A - Session 1",
        "default_amount": 5.00,
        "default_schema": "pain.001.001.03"
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