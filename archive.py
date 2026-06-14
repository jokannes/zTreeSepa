import os
import pyzipper

def MakeZip(zip_path, file_paths, password=None):
    """Bundle file_paths into a single zip at zip_path.

    When a password is given, the archive is AES-256 encrypted. Note that
    AES zips require an AES-capable extractor (7-Zip, WinRAR, PeaZip, ...);
    the Windows Explorer built-in "Extract All" cannot open them.
    When password is None/empty, a normal (unencrypted) zip is written.
    """
    if password:
        zf = pyzipper.AESZipFile(
            zip_path, "w",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        )
        zf.setpassword(password.encode("utf-8"))
    else:
        zf = pyzipper.AESZipFile(
            zip_path, "w",
            compression=pyzipper.ZIP_DEFLATED,
        )

    with zf:
        for path in file_paths:
            zf.write(path, arcname=os.path.basename(path))
