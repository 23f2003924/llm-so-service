from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import re
from typing import Optional

app = FastAPI(title="Invoice Extraction Service")

class InvoiceRequest(BaseModel):
    text: Optional[str] = None

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

@app.post("/extract", response_model=InvoiceResponse)
def extract_invoice(payload: InvoiceRequest):
    # Handle empty or malformed/missing text gracefully
    if not payload or not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid or empty invoice text provided."
        )
    
    text = payload.text

    # Robust extraction logic (can be backed by local LLM / regex parsing)
    # Vendor extraction (fallback heuristic or LLM call)
    vendor_match = re.search(r"(?:Vendor|From|Company|Name):\s*([^\n]+)", text, re.IGNORECASE)
    vendor = vendor_match.group(1).strip() if vendor_match else "Unknown Vendor"

    # Amount extraction
    amount_match = re.search(r"(?:Total|Amount Due|Balance Due|USD|EUR|GBP)?\s*\$?([0-9]+\.[0-9]{2})", text)
    if not amount_match:
        amount_match = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\b", text)
    amount = float(amount_match.group(1)) if amount_match else 0.0

    # Currency extraction (3-letter uppercase)
    curr_match = re.search(r"\b(USD|EUR|GBP|CAD|AUD)\b", text, re.IGNORECASE)
    currency = curr_match.group(1).upper() if curr_match else "USD"

    # Date extraction (YYYY-MM-DD)
    date_match = re.search(r"\b(20[2-3][0-9]-[0-1][0-9]-[0-3][0-9])\b", text)
    date_str = date_match.group(1) if date_match else "2026-01-01"

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date_str
    )
