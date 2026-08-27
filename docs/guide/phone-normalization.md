# Phone normalization

Lenco's mobile money APIs expect a Zambian number in local `0XXXXXXXXX`
shape. `normalize_zambian_phone()` gets you there from whatever shape a form
or API client hands you:

```python
from lenco.phone import normalize_zambian_phone

normalize_zambian_phone("+260966123456")  # "0966123456"
normalize_zambian_phone("260966123456")   # "0966123456"
normalize_zambian_phone("0966 123 456")   # "0966123456"
```

It's a standalone function — no client or transport involved — so you can
call it wherever you collect a phone number, before it ever reaches a
`transfers`/`collections` call.

It rejects anything that isn't a valid Zambian **mobile** number, including
landlines:

```python
normalize_zambian_phone("0211234567")  # ValueError — landline, not mobile
normalize_zambian_phone("not a phone")  # ValueError
```

Requires the `phone` extra (wraps [`phonenumbers`](https://pypi.org/project/phonenumbers/)):

```bash
pip install "lenco-py[phone]"
```

Calling it without the extra installed raises `LencoError` with that install
command in the message, not an opaque `ImportError`.

Covers Zambia only, on purpose — there's no `country=` parameter. A helper
for another country is a separate function added on its own merits, not a
case this one is meant to grow into.
