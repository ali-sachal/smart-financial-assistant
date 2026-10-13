from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException, Message, ResponseCode
from app.core.identity import get_identity_provider
from app.invoices.purchase_invoice import PurchaseInvoice
from app.repositories.subscription import user_subscription_repository
from app.utils.file_generation import high_fidelity_html_to_pdf_bytes


class InvoiceService:
    async def download(self, db: Session, subscription_id: str) -> tuple[bytes, str]:
        try:
            identifier = UUID(subscription_id)
        except ValueError as exc:
            raise AppException(ResponseCode.BAD_REQUEST, Message.INVALID_UUID) from exc
        subscription = user_subscription_repository.get_with_plan(db, identifier)
        if not subscription:
            raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND, {"subscription_id": subscription_id})
        profile = get_identity_provider().get_profile(subscription.user_id)
        invoice = PurchaseInvoice(
            first_name=profile.first_name or "Customer", last_name=profile.last_name or "",
            email=profile.email or "customer@example.com", plan_title=subscription.plan_title,
            amount_paid=float(subscription.amount_paid or 0), purchase_at=subscription.purchase_at,
            invoice_number=str(subscription.id), payment_method=("Stripe" if subscription.purchased_id else "Free"),
            payment_status=subscription.payment_status, charged_at=subscription.purchase_at,
            transaction_id=subscription.purchased_id, valid_till=subscription.expiry_at,
            plan_credits=subscription.total_credits,
        )
        content = await high_fidelity_html_to_pdf_bytes(invoice.get_html_content())
        if not content:
            raise AppException(ResponseCode.INTERNAL_SERVER_ERROR, "Invoice generation failed")
        return content, f"invoice_{invoice.invoice_number}.pdf"
