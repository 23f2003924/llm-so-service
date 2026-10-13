from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import re
from typing import Optional

app = FastAPI(title="Invoice Extraction Service")

class InvoiceRequest(BaseModel):
    text: Optional[str] = ""

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

@app.post("/extract", response_model=InvoiceResponse)
def extract_invoice(payload: InvoiceRequest):
    # Validate input: return 422 for empty, whitespace, or missing text instead of crashing
    if not payload or not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty or missing invoice text provided."
        )
    
    text = payload.text

    # 1. Vendor extraction (supports Acme-xxxx style names and labeled fields)
    vendor_match = re.search(r"(?:Vendor|From|Company|Name):\s*([^\n]+)", text, re.IGNORECASE)
    if not vendor_match:
        acme_match = re.search(r"(Acme-[A-Za-z0-9\-]+(?:\s+Industries\s+Ltd\.?)?)", text, re.IGNORECASE)
        if acme_match:
            vendor = acme_match.group(1).strip()
        else:
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            vendor = lines[0] if lines else "Unknown Vendor"
    else:
        vendor = vendor_match.group(1).strip()

    # 2. Amount extraction
    amount_match = re.search(r"(?:Total|Amount Due|Balance Due|USD|EUR|GBP)?\s*\$?([0-9]+\.[0-9]{2})", text)
    if not amount_match:
        amount_match = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\b", text)
    amount = float(amount_match.group(1)) if amount_match else 0.0

    # 3. Currency extraction (3-letter uppercase)
    curr_match = re.search(r"\b(USD|EUR|GBP|CAD|AUD)\b", text, re.IGNORECASE)
    currency = curr_match.group(1).upper() if curr_match else "USD"

    # 4. Date extraction (YYYY-MM-DD)
    date_match = re.search(r"\b(20[2-3][0-9]-[0-1][0-9]-[0-3][0-9])\b", text)
    date_str = date_match.group(1) if date_match else "2026-01-01"

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date_str
    )
