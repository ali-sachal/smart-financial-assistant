import argparse
import getpass

import boto3

from app.core.config import settings


def create_demo_user(email: str, password: str) -> None:
    if not settings.COGNITO_USER_POOL_ID:
        raise RuntimeError("COGNITO_USER_POOL_ID is required")
    client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)
    try:
        client.admin_create_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[{"Name": "email", "Value": email}, {"Name": "email_verified", "Value": "true"}],
            MessageAction="SUPPRESS",
        )
    except client.exceptions.UsernameExistsException:
        pass
    client.admin_set_user_password(
        UserPoolId=settings.COGNITO_USER_POOL_ID,
        Username=email,
        Password=password,
        Permanent=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset the pre-confirmed Cognito demo user.")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Demo user password: ")
    if len(password) < 12:
        raise RuntimeError("Password must contain at least 12 characters")
    create_demo_user(args.email, password)
    print(f"Demo user is ready: {args.email}")


if __name__ == "__main__":
    main()
