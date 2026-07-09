from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, RefreshToken
from app.models.role import Role
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        query = (
            select(User)
            .where(User.email == email, User.deleted_at.is_(None))
            .options(selectinload(User.role), selectinload(User.doctor))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        query = (
            select(User)
            .where(User.username == username, User.deleted_at.is_(None))
            .options(selectinload(User.role), selectinload(User.doctor))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_with_role(self, user_id: str) -> User | None:
        query = (
            select(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .options(selectinload(User.role), selectinload(User.doctor))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_with_role(self, skip: int = 0, limit: int = 100) -> list[User]:
        query = (
            select(User)
            .where(User.deleted_at.is_(None))
            .options(selectinload(User.role), selectinload(User.doctor))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: AsyncSession):
        super().__init__(Role, db)

    async def get_by_name(self, name: str) -> Role | None:
        query = select(Role).where(Role.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(RefreshToken, db)

    async def get_by_token(self, token: str) -> RefreshToken | None:
        query = (
            select(RefreshToken)
            .where(RefreshToken.token == token)
            .options(selectinload(RefreshToken.user).selectinload(User.role))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
