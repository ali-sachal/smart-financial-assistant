from pathlib import Path
from datetime import datetime
from typing import Optional, List, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.config import settings


class PurchaseInvoice:
    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        plan_title: str,
        amount_paid: float,
        purchase_at: datetime,
        invoice_number: Optional[str] = None,
        payment_method: str = "Stripe",
        modules_details: Optional[List[Any]] = None,
        payment_status: str = "Paid",
        charged_at: Optional[datetime] = None,
        transaction_id: Optional[str] = None,
        valid_till: Optional[datetime] = None,
        discount_amount: float = 0.0,
        plan_credits: int = 0
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.plan_title = plan_title
        self.amount_paid = amount_paid
        self.purchase_at = purchase_at
        self.invoice_number = invoice_number or purchase_at.strftime("%Y%m%d%H%M%S")
        self.payment_method = payment_method
        self.modules_details = modules_details or []
        self.payment_status = payment_status
        self.charged_at = charged_at or purchase_at
        self.transaction_id = transaction_id or "-"
        self.valid_till = valid_till
        self.discount_amount = discount_amount
        self.plan_credits = plan_credits

    def get_html_content(self) -> str:
        templates_path = Path(__file__).parent / "templates"
        env = Environment(
            loader=FileSystemLoader(str(templates_path)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("purchase_invoice.html")

        amount_formatted = f"{self.amount_paid:.2f}"
        purchase_date = self.purchase_at.strftime("%d/%m/%Y")

        total_amount_formatted = amount_formatted
        discount_amount_formatted = f"{self.discount_amount:.2f}"
        total_paid_amount_formatted = f"{(self.amount_paid):.2f}"
        paid_in_full = True
        charged_at_str = self.charged_at.strftime("%d/%m/%Y %H:%M")
        valid_till_str = self.valid_till.strftime("%d/%m/%Y") if self.valid_till else "-"

        return template.render(
            app_name=settings.APP_NAME,
            business_name=settings.INVOICE_BUSINESS_NAME,
            business_identifier=settings.INVOICE_BUSINESS_IDENTIFIER,
            business_email=settings.INVOICE_BUSINESS_EMAIL,
            business_address=settings.INVOICE_BUSINESS_ADDRESS,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            plan_title=self.plan_title,
            amount_formatted=amount_formatted,
            purchase_date=purchase_date,
            invoice_number=self.invoice_number,
            payment_method=self.payment_method,
            total_amount_formatted=total_amount_formatted,
            total_paid_amount_formatted=total_paid_amount_formatted,
            discount_amount_formatted=discount_amount_formatted,
            paid_in_full=paid_in_full,
            payment_status=self.payment_status,
            charged_at=charged_at_str,
            transaction_id=self.transaction_id,
            valid_till=valid_till_str,
            plan_credits=self.plan_credits,
        )
