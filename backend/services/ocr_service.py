# backend/services/ocr_service.py
from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path
from PIL import Image
import pytesseract

def ocr_pdf_bytes(pdf_bytes: bytes, lang: str = "spa") -> str:
    MAX_PAGES = 40

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pdf_path = td / "doc.pdf"
        pdf_path.write_bytes(pdf_bytes)

        out_prefix = td / "page"

        try:
            subprocess.run(
                ["pdftoppm", "-png", "-r", "200", str(pdf_path), str(out_prefix)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("OCR timeout (pdftoppm)")
        except FileNotFoundError:
            raise RuntimeError("pdftoppm no está instalado")

        textos = []

        for i, img_path in enumerate(sorted(td.glob("page-*.png"))):
            if i >= MAX_PAGES:
                break

            img = Image.open(img_path).convert("L")
            textos.append(pytesseract.image_to_string(img, lang=lang))

        texto_final = "\n".join(textos)
        texto_final = re.sub(r"\n{3,}", "\n\n", texto_final)

        return texto_final.strip()
