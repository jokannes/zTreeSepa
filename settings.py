import os
import json
from tkinter import messagebox

DEFAULT_SCHEMA = "pain.001.001.09"

SUPPORTED_SCHEMAS = {
    "pain.001.001.09": "SEPA standard as of Nov 2026 (default)",
    "pain.001.001.03": "Legacy format, phased out as of Nov 2026",
    "pain.001.001.10": "Newer ISO 20022 version - use only if agreed with bank",
    "pain.001.001.11": "Newer ISO 20022 version - use only if agreed with bank",
}

def LoadSettings(SETTINGS_FILE):
    default_settings = {
        "payer_name": "My Company GmbH",
        "payer_iban": "DE02100100109307118603",
        "payer_bic": "PBNKDEFFXXX",
        "currency": "EUR",
        "placeholder_reference": "e.g., Lab Payment 10 July 2025 - 10am",
        "placeholder_experiment": "e.g., Study A - Session 1",
        "default_amount": 5.00,
        "default_schema": DEFAULT_SCHEMA
    }

    if not os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create default settings.json: {e}")
            return default_settings

    try:
        # utf-8-sig also tolerates a BOM, which Notepad may add when users edit the file
        with open(SETTINGS_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load settings.json: {e}")
        return default_settings
    
def SaveSettings(SETTINGS_FILE, settings):
    tmp_file = SETTINGS_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        os.replace(tmp_file, SETTINGS_FILE)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Could not save settings.json: {e}")
        return False