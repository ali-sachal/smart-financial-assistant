from pydantic import BaseModel, Field


class AuthenticatedUser(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    email: str | None = None
    username: str | None = None
    scopes: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
