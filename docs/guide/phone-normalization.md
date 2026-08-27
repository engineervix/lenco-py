# Phone normalization

Lenco's mobile money APIs expect a Zambian number in local `0XXXXXXXXX`
shape. `normalize_zambian_phone()` converts whatever shape a form or API
client gives you to that shape:

```python
from lenco.phone import normalize_zambian_phone

normalize_zambian_phone("+260966123456")  # "0966123456"
normalize_zambian_phone("260966123456")   # "0966123456"
normalize_zambian_phone("0966 123 456")   # "0966123456"
```

It is a standalone function. It does not use the client or the transport.
You can call it wherever you collect a phone number, before the number
reaches a `transfers` or `collections` call.

It rejects anything that is not a valid Zambian **mobile** number, including
landlines:

```python
normalize_zambian_phone("0211234567")  # ValueError — landline, not mobile
normalize_zambian_phone("not a phone")  # ValueError
```

It requires the `phone` extra, which wraps
[`phonenumbers`](https://pypi.org/project/phonenumbers/):

```bash
pip install "lenco-py[phone]"
```

If the extra is not installed, it raises `LencoError` with the install
command in the message, instead of an opaque `ImportError`.

It covers Zambia only, on purpose. There is no `country=` parameter. A
helper for another country is a separate function, added on its own merits
later — not something this function is meant to grow into.
