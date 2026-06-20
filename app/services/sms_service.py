import os
import requests
import logging

logger = logging.getLogger(__name__)


class SMSService:

    TEXTBELT_URL = "https://textbelt.com/text"

    @classmethod
    def send_bill(cls, to_phone: str, bill_id: int, total_amount: float,
                  customer_name: str = None, loyalty_points_earned: int = 0) -> bool:
        """
        Send bill summary SMS via TextBelt free API.
        Currently disabled — TextBelt free tier does not support Indian numbers.
        Phone number is still recorded in the database for future SMS integration.
        Returns False (SMS not sent).
        """
        # SMS sending is disabled for now (TextBelt free doesn't support Indian numbers).
        # Phone number is already saved in bills.customer_phone and customers.phone.
        # To enable: swap to Fast2SMS or Twilio and update this method.
        logger.info(f"SMS disabled — phone {to_phone} recorded for bill #{bill_id} (Rs.{total_amount:.2f})")
        return False
