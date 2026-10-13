import argparse
import logging
from datetime import date, datetime, timedelta

from app.db.session import SessionLocal
from app.models.user import Users
from app.repositories.subscription import user_subscription_repository


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_cutoff() -> datetime:
    return datetime.combine(date.today() - timedelta(days=1), datetime.min.time())


def disable_failed_pending_auto_subscriptions(commit: bool = False) -> int:
    db = SessionLocal()
    try:
        cutoff = get_cutoff()
        user_ids = user_subscription_repository.get_failed_or_pending_latest_purchase_expired_paid_user_ids(
            db,
            cutoff,
        )

        logger.info("Found %s eligible users with paid subscriptions expired before %s.", len(user_ids), cutoff)
        if user_ids:
            logger.info("Eligible user_ids: %s", ", ".join(user_ids))

        if not commit or not user_ids:
            if not commit:
                logger.info("Dry run only. Re-run with --commit to set users.auto_sub = false.")
            return len(user_ids)

        updated_count = (
            db.query(Users)
            .filter(
                Users.user_id.in_(user_ids),
                Users.auto_sub == True,
            )
            .update({Users.auto_sub: False}, synchronize_session=False)
        )
        db.commit()

        logger.info("Updated %s users: set users.auto_sub = false.", updated_count)
        return updated_count
    except Exception:
        db.rollback()
        logger.exception("Failed to disable auto subscriptions.")
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Set users.auto_sub = false for users whose latest purchase is failed/pending "
            "and whose paid subscriptions all expired before today()-1."
        )
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Apply the update. Without this flag the script only reports eligible users.",
    )
    args = parser.parse_args()

    disable_failed_pending_auto_subscriptions(commit=args.commit)


if __name__ == "__main__":
    main()
