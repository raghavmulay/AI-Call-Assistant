import asyncio
from backend.app.database.database import AsyncSessionLocal
from backend.app.auth.hashing import hash_password
from backend.app.auth.jwt_handler import create_access_token
from backend.app.models.student import Student, Role
from backend.app.schemas.auth import TokenResponse
import uuid

async def test():
    async with AsyncSessionLocal() as db:
        # Simulate exactly what the signup endpoint does
        student = Student(
            name="Test2",
            email="test2_unique@vit.edu",
            hashed_password=hash_password("test1234"),
            branch="computer engineering",
            year=2,
            division="A",
            role=Role.student,
        )
        db.add(student)
        await db.flush()
        await db.refresh(student)
        await db.commit()
        print(f"DB insert OK, id={student.id}, role={student.role}, role.value={student.role.value}")

        token = create_access_token({"sub": str(student.id), "role": student.role.value})
        print(f"JWT OK: {token[:40]}...")

        # Simulate Pydantic response serialization
        resp = TokenResponse(access_token=token, role=student.role.value, user_id=student.id)
        print(f"Pydantic OK: {resp.model_dump()}")

asyncio.run(test())
