"""Response fixtures built from the Lenco API docs' example payloads."""

BANK = {"id": "002", "name": "Absa Bank", "country": "zm"}

RECIPIENT_MOBILE_MONEY = {
    "id": "d6b6e00e-bdb6-43a6-a561-85b61496198e",
    "details": {
        "type": "mobile-money",
        "accountName": "Beata Jean",
        "phone": "0750000000",
        "operator": "zamtel",
    },
    "currency": "ZMW",
    "type": "mobile-money",
    "country": "zm",
}

RECIPIENT_BANK_ACCOUNT = {
    "id": "d4f71d4a-eda4-4237-9976-5cbdc8a54cf3",
    "details": {
        "type": "bank-account",
        "accountName": "Beata Jean",
        "accountNumber": "9130000000000",
        "bank": BANK,
    },
    "currency": "ZMW",
    "type": "bank-account",
    "country": "zm",
}

TRANSFER = {
    "id": "9525b4c6-502b-45be-90e1-81eb81a3f424",
    "amount": "20.00",
    "fee": "8.50",
    "currency": "ZMW",
    "narration": "Transfer",
    "initiatedAt": "2024-01-01T00:00:00.447Z",
    "completedAt": "2024-01-01T00:00:01.237Z",
    "accountId": "b176cda5-7d97-4a3f-b4dd-ab0234e9e08c",
    "creditAccount": {
        "type": "bank-account",
        "accountName": "Beata Jean",
        "accountNumber": "9130000000000",
        "bank": BANK,
    },
    "status": "successful",
    "reasonForFailure": None,
    "reference": "ref-3",
    "lencoReference": "240010002",
    "extraData": {"nipSessionId": None},
    "source": "api",
}

COLLECTION = {
    "id": "d7bd9ccb-0737-4e72-a387-d00454341f21",
    "initiatedAt": "2024-03-12T07:06:11.562Z",
    "completedAt": "2024-03-12T07:14:10.412Z",
    "amount": "10.00",
    "fee": "0.25",
    "bearer": "merchant",
    "currency": "ZMW",
    "reference": "ref-1",
    "lencoReference": "240720004",
    "type": "mobile-money",
    "status": "successful",
    "source": "api",
    "reasonForFailure": None,
    "settlementStatus": "settled",
    "settlement": {
        "id": "c04583d7-d026-4dfa-b8b5-e96f17f93bb8",
        "amountSettled": "9.75",
        "currency": "ZMW",
        "createdAt": "2024-03-12T07:14:10.439Z",
        "settledAt": "2024-03-12T07:14:10.496Z",
        "status": "settled",
        "type": "instant",
        "accountId": "68f11209-451f-4a15-bfcd-d916eb8b09f4",
    },
    "mobileMoneyDetails": {
        "country": "zm",
        "phone": "0977433571",
        "operator": "airtel",
        "accountName": "Beata Jean",
        "operatorTransactionId": "MP240312.0000.A00001",
    },
    "bankAccountDetails": None,
    "cardDetails": None,
}

SETTLEMENT = {
    "id": "c04583d7-d026-4dfa-b8b5-e96f17f93bb8",
    "amountSettled": "9.75",
    "currency": "ZMW",
    "createdAt": "2024-03-12T07:14:10.439Z",
    "settledAt": "2024-03-12T07:14:10.496Z",
    "status": "settled",
    "type": "instant",
    "accountId": "68f11209-451f-4a15-bfcd-d916eb8b09f4",
    "collection": COLLECTION,
}

TRANSACTION = {
    "id": "d6730fe6-77a0-4432-a283-832eaef31786",
    "amount": "13.00",
    "currency": "ZMW",
    "narration": "Transfer / 240730006",
    "type": "debit",
    "datetime": "2024-01-10T14:24:31.931Z",
    "accountId": "b176cda5-7d97-4a3f-b4dd-ab0234e9e08c",
    "balance": "997559.00",
}

META = {"total": 1, "pageCount": 1, "perPage": 100, "currentPage": 1}

ENCRYPTION_KEY = {
    "kty": "RSA",
    "use": "enc",
    "n": "nApb8LyyFrZw4AW1RpGR6Z7zcNikiZcQ",
    "e": "AQAB",
    "kid": "2bbb0d2f68aa",
}

PUBLIC_FIXTURES = {
    "account": {
        "id": "b176cda5-7d97-4a3f-b4dd-ab0234e9e08c",
        "details": {
            "type": "lenco-merchant",
            "accountName": "Account Name",
            "tillNumber": "0000001",
        },
        "type": "Lenco Merchant",
        "status": "active",
        "createdAt": "2024-01-01T00:00:00.000Z",
        "currency": "ZMW",
        "availableBalance": "0.00",
        "ledgerBalance": "0.00",
    }
}


def envelope(data, meta=None):
    """Wrap a payload in the Lenco response envelope."""
    body = {"status": True, "message": "", "data": data}
    if meta is not None:
        body["meta"] = meta
    return body
