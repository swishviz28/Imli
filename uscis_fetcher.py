import requests

def download_pdf_bytes(url: str) -> bytes:
    """
    Download a PDF from a given URL and return its raw bytes.
    Assumes the URL points directly to a PDF on a site like USCIS/AAO.
    """
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "pdf" not in content_type.lower():
        raise ValueError(f"URL does not appear to be a PDF. Content-Type: {content_type}")

    return resp.content
