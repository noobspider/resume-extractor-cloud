def detect_phones(text, region="IN"):
    phones = []
    try:
        for m in phonenumbers.PhoneNumberMatcher(text, region):
            phones.append(phonenumbers.format_number(m.number, phonenumbers.PhoneNumberFormat.E164))
    except Exception:
        pass
    return list(dict.fromkeys(phones))
