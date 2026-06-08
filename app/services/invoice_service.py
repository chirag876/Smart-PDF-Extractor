import re

def parse_invoice(text: str) -> dict:
    return {
        "vendor": extract_vendor(text),
        "bill_to": extract_bill_to(text),
        "total_amount": extract_total(text),
        "payment_terms": extract_payment_terms(text),
        "items": extract_items(text)
    }

def extract_total(text: str) -> str:
    match = re.search(r'TOTAL\s*:\s*RS[:\s]*([\d,]+)', text, re.IGNORECASE)
    return match.group(1).replace(',', '') if match else None

import re

def extract_vendor(text: str) -> str:
    match = re.search(r'FROM\s*\n([A-Z\s]+(?:PRIVATE LIMITED|LTD|LLC|INC)?)', text)
    return match.group(1).strip() if match else None

def extract_bill_to(text: str) -> str:
    match = re.search(r'BILL TO\s*\n([A-Z\s]+(?:PRIVATE LIMITED|LTD|LLC|INC)?)', text)
    return match.group(1).strip() if match else None

def extract_payment_terms(text: str) -> str:
    match = re.search(r'(Payment is due[^\n]+)', text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_bank_details(text: str) -> dict:
    bank = re.search(r'(State bank of india|HDFC|ICICI|Axis Bank)', text, re.IGNORECASE)
    account = re.search(r'Account number[:\s]+([A-Z0-9]+)', text, re.IGNORECASE)
    ifsc = re.search(r'IFSC[:\s]+([A-Z0-9]+)', text, re.IGNORECASE)
    return {
        "bank": bank.group(1) if bank else None,
        "account_number": account.group(1) if account else None,
        "ifsc": ifsc.group(1) if ifsc else None
    }

def extract_items(text: str) -> list:
    items = []
    pattern = re.findall(r'(\d+)\s+([A-Za-z\s]+?)\s+(\d+\s*\w+)\s+([\d.]+%)\s+([\d.]+%)\s+(\d+)', text)
    for match in pattern:
        items.append({
            "sno": int(match[0]),
            "name": match[1].strip(),
            "qty": match[2].strip(),
            "discount": match[3],
            "tax": match[4],
            "price": int(match[5])
        })
    return items
