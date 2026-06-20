import os
import requests
import logging

logger = logging.getLogger(__name__)


class EmailService:

    BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

    @classmethod
    def send_bill(cls, to_email: str, bill_id: int, total_amount: float,
                  items: list, customer_name: str = None,
                  loyalty_points_earned: int = 0, customer_total_points: int = 0) -> bool:
        """
        Send HTML bill receipt via Brevo transactional email API.
        Returns True on success, False on failure (bill is already saved — no rollback).
        """
        api_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL", "noreply@smartretail.com")
        sender_name = os.getenv("BREVO_SENDER_NAME", "Smart Retail")

        if not api_key:
            logger.warning("BREVO_API_KEY not set. Skipping email.")
            return False

        display_name = customer_name or "Valued Customer"
        bill_number = f"SR-{str(bill_id).zfill(6)}"

        # Build items table rows
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;">{item.get('name', f"Product #{item.get('product_id')}")}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;">{item.get('quantity')}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;">&#8377;{float(item.get('unit_price', 0)):.2f}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;font-weight:600;">&#8377;{float(item.get('subtotal', 0)):.2f}</td>
            </tr>"""

        # Loyalty section
        loyalty_html = ""
        if loyalty_points_earned > 0:
            loyalty_html = f"""
            <div style="margin:16px 0;padding:12px 16px;background:#e6f4ea;border-radius:6px;border-left:4px solid #2E8B57;">
                <strong style="color:#2E8B57;">&#127881; Loyalty Points Earned: +{loyalty_points_earned} pts</strong><br>
                <span style="font-size:13px;color:#555;">Total Points: {customer_total_points} pts (1 pt per &#8377;10 spent)</span>
            </div>"""

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#f5f5f5;font-family:'Segoe UI',Arial,sans-serif;">
          <div style="max-width:540px;margin:32px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

            <!-- Header -->
            <div style="background:#2E8B57;padding:28px 32px;">
              <h1 style="margin:0;color:#fff;font-size:22px;font-weight:800;letter-spacing:-0.5px;">Smart Retail</h1>
              <p style="margin:4px 0 0;color:rgba(255,255,255,0.8);font-size:13px;">Your bill receipt</p>
            </div>

            <!-- Body -->
            <div style="padding:28px 32px;">
              <p style="font-size:15px;color:#333;">Hi <strong>{display_name}</strong>,</p>
              <p style="font-size:14px;color:#555;">Thank you for shopping with us! Here is your bill summary.</p>

              <!-- Bill Meta -->
              <table style="width:100%;margin:16px 0;font-size:13px;color:#555;">
                <tr>
                  <td><strong>Bill No:</strong> {bill_number}</td>
                  <td style="text-align:right;"><strong>Total:</strong> <span style="color:#2E8B57;font-size:16px;font-weight:800;">&#8377;{total_amount:.2f}</span></td>
                </tr>
              </table>

              <!-- Items Table -->
              <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                  <tr style="background:#f5f5f5;">
                    <th style="padding:10px 12px;text-align:left;color:#555;font-weight:700;border-bottom:2px solid #e5e5e5;">Item</th>
                    <th style="padding:10px 12px;text-align:center;color:#555;font-weight:700;border-bottom:2px solid #e5e5e5;">Qty</th>
                    <th style="padding:10px 12px;text-align:right;color:#555;font-weight:700;border-bottom:2px solid #e5e5e5;">Price</th>
                    <th style="padding:10px 12px;text-align:right;color:#555;font-weight:700;border-bottom:2px solid #e5e5e5;">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {items_html}
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="3" style="padding:12px;text-align:right;font-weight:800;font-size:15px;">Grand Total</td>
                    <td style="padding:12px;text-align:right;font-weight:800;font-size:15px;color:#2E8B57;">&#8377;{total_amount:.2f}</td>
                  </tr>
                </tfoot>
              </table>

              {loyalty_html}

              <p style="font-size:12px;color:#888;margin-top:24px;text-align:center;">
                Smart Retail &bull; This is an automated bill receipt.<br>
                Please do not reply to this email.
              </p>
            </div>
          </div>
        </body>
        </html>
        """

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": to_email, "name": display_name}],
            "subject": f"Your Bill from Smart Retail — {bill_number}",
            "htmlContent": html_content
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": api_key
        }

        try:
            response = requests.post(cls.BREVO_API_URL, json=payload, headers=headers, timeout=10)
            if response.status_code in (200, 201):
                logger.info(f"Bill email sent to {to_email} for bill #{bill_id}")
                return True
            else:
                logger.error(f"Brevo email failed: {response.status_code} — {response.text}")
                return False
        except Exception as e:
            logger.error(f"Email sending exception: {e}")
            return False
