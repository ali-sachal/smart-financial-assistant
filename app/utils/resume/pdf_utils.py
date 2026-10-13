
def is_pdf_bytes(data: bytes) -> bool:
    return isinstance(data, (bytes, bytearray)) and data[:4] == b"%PDF"


def make_simple_pdf_from_text(text: str) -> bytes:
    lines = text.split("\n")
    objects = []
    offsets = []
    def add_obj(s: str) -> None:
        offsets.append(sum(len(o) for o in objects))
        objects.append(s)
    header = b"%PDF-1.4\n"
    font_obj = "4 0 obj\n<< /Type /Font /Subtype /Type1 /Name /F1 /BaseFont /Helvetica >>\nendobj\n"
    add_obj(font_obj)
    content_lines = []
    content_lines.append("BT\n/F1 12 Tf\n")
    y = 800
    for line in lines:
        safe = line.replace("(", "\\(").replace(")", "\\)")
        content_lines.append(f"50 {y} Td ({safe}) Tj\n")
        y -= 14
        if y < 50:
            break
    content_lines.append("ET\n")
    stream_data = "".join(content_lines).encode("utf-8")
    content_obj = f"5 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("utf-8") + stream_data + b"endstream\nendobj\n"
    add_obj(content_obj.decode("latin1"))
    page_obj = "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
    add_obj(page_obj)
    pages_obj = "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    add_obj(pages_obj)
    catalog_obj = "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    add_obj(catalog_obj)
    xref_offset = len(header) + sum(len(o) for o in objects)
    xref = ["xref\n0 6\n", "0000000000 65535 f \n"]
    for off in [0] + offsets:
        xref.append(f"{off+len(header):010d} 00000 n \n")
    trailer = "trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref_offset) + "\n%%EOF\n"
    body = header + "".join(objects).encode("latin1") + "".join(xref).encode("latin1") + trailer.encode("latin1")
    return body

