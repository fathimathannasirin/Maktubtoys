from django import forms


def normalize_qatar_phone(value, required=False):
    raw = (value or '').strip()
    if not raw:
        if required:
            raise forms.ValidationError('Please enter your phone number.')
        return ''

    # Accept common formatting like +974 12345678 or +974-1234-5678.
    digits = ''.join(str(int(char)) for char in raw if char.isdigit())
    if not digits:
        raise forms.ValidationError('Please enter exactly 8 digits after +974.')

    if len(digits) == 11 and digits.startswith('974'):
        digits = digits[3:]

    if len(digits) != 8:
        raise forms.ValidationError('Please enter exactly 8 digits after +974.')

    return f'+974{digits}'