from decimal import Decimal
from mailjet_rest import Client
from django.conf import settings
import base64

api_key = settings.MAILJET_API_KEY  # Set these in your settings.py
api_secret = settings.MAILJET_API_SECRET
mailjet = Client(auth=(api_key, api_secret), version='v3.1')

COUNTRY_CURRENCY = {
    "United Arab Emirates": "AED",
    "India": "INR",
    "USA": "USD",
    "United Kingdom": "GBP",
    "Saudi Arabia": "SAR",
    "Kuwait": "KWD",
    "Qatar": "QAR",
    "Oman": "OMR",
    "Bahrain": "BHD",
    "Other": "USD",
}

CURRENCY_SYMBOL = {
    "AED": "د.إ",
    "INR": "₹",
    "USD": "$",
    "GBP": "£",
    "SAR": "ر.س",
    "KWD": "د.ك",
    "QAR": "ر.ق",
    "OMR": "ر.ع",
    "BHD": "ب.د",
}

def number_to_words(amount, currency="USD"):
    import math
    from num2words import num2words

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    whole = int(math.floor(amount))
    fraction = int(round((amount - whole) * 100))

    words = num2words(whole, to='cardinal', lang='en').capitalize()
    currency_name = currency_name_from_code(currency)

    if fraction > 0:
        if currency == "AED":
            return f"{words} {currency_name} and {fraction} fils"
        return f"{words} {currency_name} and {fraction}/100"
    return f"{words} {currency_name}"

def currency_name_from_code(code):
    return {
        "AED": "Dirhams",
        "INR": "Rupees",
        "USD": "Dollars",
        "GBP": "Pounds",
        "SAR": "Riyals",
        "KWD": "Dinars",
        "QAR": "Riyals",
        "OMR": "Rials",
        "BHD": "Dinars",
    }.get(code, "Dollars")

def send_mailjet_email(subject, body, to_email, attachments=None):
    from_name = "SHEROOK KALBA"  # Your shop name
    from_email = "rejiojoel4@outlook.com"  # Your Mailjet sender email

    # Mailjet expects From as "Name <email>"
    # mailjet_from = f"{from_name} <{from_email}>"

    data = {
        "Messages": [
            {
                "From": {
                    "Email": from_email,
                    "Name": from_name
                },
                "To": [{"Email": to_email}],
                "Subject": subject,
                "TextPart": body,
                "HTMLPart": body,
                # ...attachments if any...
            }
        ]
    }
    result = mailjet.send.create(data=data)
    return result.status_code, result.json()

from mailjet_rest import Client
from django.conf import settings

def send_mailjet_email(from_email, to_email, subject, body):
    mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET), version='v3.1')
    data = {
      'Messages': [
        {
          "From": {
            "Email": from_email,
            "Name": "High Speed Graphics"
          },
          "To": [
            {
              "Email": to_email,
              "Name": "Customer"
            }
          ],
          "Subject": subject,
          "TextPart": body,
        }
      ]
    }
    result = mailjet.send.create(data=data)
    return result.status_code == 200