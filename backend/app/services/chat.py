"""Chat message service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


class ChatService:
    """Service for chat message CRUD operations."""

    @staticmethod
    async def list_file_messages(
        db: AsyncSession,
        file_id: UUID,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[ChatMessage], int]:
        """List chat messages for a specific file.

        Args:
            db: Database session
            file_id: File UUID
            user_id: User UUID (for isolation check)
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            Tuple of (messages list, total count)
        """
        # Query messages with pagination
        result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.file_id == file_id,
                ChatMessage.user_id == user_id
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        messages = list(result.scalars().all())

        # Query total count
        count_result = await db.execute(
            select(func.count(ChatMessage.id))
            .where(
                ChatMessage.file_id == file_id,
                ChatMessage.user_id == user_id
            )
        )
        total_count = count_result.scalar_one()

        return messages, total_count

    @staticmethod
    async def create_message(
        db: AsyncSession,
        file_id: UUID,
        user_id: UUID,
        content: str,
        role: str = "user",
        message_type: str | None = None,
        metadata_json: dict | None = None
    ) -> ChatMessage:
        """Create a new chat message.

        Args:
            db: Database session
            file_id: File UUID
            user_id: User UUID
            content: Message content
            role: Message role (user or assistant)
            message_type: Optional message type
            metadata_json: Optional metadata dictionary

        Returns:
            Created ChatMessage record
        """
        message = ChatMessage(
            file_id=file_id,
            user_id=user_id,
            content=content,
            role=role,
            message_type=message_type,
            metadata_json=metadata_json
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        return message

    @staticmethod
    async def list_session_messages(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[ChatMessage], int]:
        """List chat messages for a specific session.

        Args:
            db: Database session
            session_id: Session UUID
            user_id: User UUID (for isolation check)
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            Tuple of (messages list, total count)
        """
        # Query messages with pagination
        result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == user_id
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        messages = list(result.scalars().all())

        # Query total count
        count_result = await db.execute(
            select(func.count(ChatMessage.id))
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == user_id
            )
        )
        total_count = count_result.scalar_one()

        return messages, total_count

    @staticmethod
    async def create_session_message(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        content: str,
        role: str = "user",
        message_type: str | None = None,
        metadata_json: dict | None = None
    ) -> ChatMessage:
        """Create a new chat message for a session.

        Args:
            db: Database session
            session_id: Session UUID
            user_id: User UUID
            content: Message content
            role: Message role (user or assistant)
            message_type: Optional message type
            metadata_json: Optional metadata dictionary

        Returns:
            Created ChatMessage record
        """
        message = ChatMessage(
            session_id=session_id,
            file_id=None,  # Messages now belong to sessions, not files
            user_id=user_id,
            content=content,
            role=role,
            message_type=message_type,
            metadata_json=metadata_json
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        return message
