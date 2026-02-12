"""Chat session service layer for CRUD operations and file linking."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession
from app.models.file import File


class ChatSessionService:
    """Service for chat session CRUD operations and file linking."""

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: UUID,
        title: str
    ) -> ChatSession:
        """Create a new chat session.

        Args:
            db: Database session
            user_id: User UUID
            title: Session title

        Returns:
            Created ChatSession record
        """
        session = ChatSession(
            user_id=user_id,
            title=title
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session

    @staticmethod
    async def list_user_sessions(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[ChatSession], int]:
        """List chat sessions for a user.

        Args:
            db: Database session
            user_id: User UUID (for isolation check)
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            Tuple of (sessions list, total count)
        """
        # Query sessions with pagination, eager load files for file_count
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.files))
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        sessions = list(result.scalars().all())

        # Query total count
        count_result = await db.execute(
            select(func.count(ChatSession.id))
            .where(ChatSession.user_id == user_id)
        )
        total_count = count_result.scalar_one()

        return sessions, total_count

    @staticmethod
    async def get_user_session(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID
    ) -> ChatSession | None:
        """Get a specific session for a user.

        Args:
            db: Database session
            session_id: Session UUID
            user_id: User UUID (for isolation check)

        Returns:
            ChatSession record if found and belongs to user, None otherwise
        """
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.files))
            .where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_session(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        title: str | None = None
    ) -> ChatSession | None:
        """Update a chat session.

        Args:
            db: Database session
            session_id: Session UUID
            user_id: User UUID (for isolation check)
            title: New title (if provided)

        Returns:
            Updated ChatSession record or None if not found
        """
        # Get session with ownership check
        session = await ChatSessionService.get_user_session(db, session_id, user_id)

        if session is None:
            return None

        # Update fields
        if title is not None:
            session.title = title
            session.user_modified = True  # Lock title from auto-generation

        await db.commit()
        await db.refresh(session)

        return session

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a chat session.

        Args:
            db: Database session
            session_id: Session UUID
            user_id: User UUID (for isolation check)

        Returns:
            True if session was deleted, False if not found

        Note:
            Cascade deletes related messages (per model config).
        """
        # Get session with ownership check
        session = await ChatSessionService.get_user_session(db, session_id, user_id)

        if session is None:
            return False

        await db.delete(session)
        await db.commit()

        return True

    @staticmethod
    async def link_file_to_session(
        db: AsyncSession,
        session_id: UUID,
        file_id: UUID,
        user_id: UUID
    ) -> ChatSession:
        """Link a file to a chat session.

        Args:
            db: Database session
            session_id: Session UUID
            file_id: File UUID
            user_id: User UUID (for ownership checks)

        Returns:
            Updated ChatSession record

        Raises:
            ValueError: If session or file not found, file already linked, or file limit exceeded
        """
        # Get session with ownership check
        session = await ChatSessionService.get_user_session(db, session_id, user_id)

        if session is None:
            raise ValueError("Session not found")

        # Get file with ownership check
        file_result = await db.execute(
            select(File).where(
                File.id == file_id,
                File.user_id == user_id
            )
        )
        file = file_result.scalar_one_or_none()

        if file is None:
            raise ValueError("File not found")

        # Check if file already linked
        if file in session.files:
            raise ValueError("File already linked to session")

        # Check configurable file count limit from settings.yaml
        from app.services.context_assembler import load_session_settings
        settings = load_session_settings()
        max_files = settings["session"]["max_files_per_session"]

        if len(session.files) >= max_files:
            raise ValueError(f"Maximum {max_files} files per session")

        # Check total file size limit
        max_size_bytes = settings["session"]["max_total_file_size_mb"] * 1024 * 1024
        current_total = sum(f.file_size for f in session.files)
        if current_total + file.file_size > max_size_bytes:
            max_mb = settings["session"]["max_total_file_size_mb"]
            raise ValueError(f"Total file size would exceed {max_mb}MB limit")

        # Link file to session
        session.files.append(file)

        await db.commit()
        await db.refresh(session)

        return session

    @staticmethod
    async def unlink_file_from_session(
        db: AsyncSession,
        session_id: UUID,
        file_id: UUID,
        user_id: UUID
    ) -> ChatSession:
        """Unlink a file from a chat session.

        Args:
            db: Database session
            session_id: Session UUID
            file_id: File UUID
            user_id: User UUID (for ownership check)

        Returns:
            Updated ChatSession record

        Raises:
            ValueError: If session not found or file not linked

        Note:
            This does NOT delete messages (DATA-06) - messages stay with session.
        """
        # Get session with ownership check
        session = await ChatSessionService.get_user_session(db, session_id, user_id)

        if session is None:
            raise ValueError("Session not found")

        # Find file in session.files
        file_to_remove = None
        for file in session.files:
            if file.id == file_id:
                file_to_remove = file
                break

        if file_to_remove is None:
            raise ValueError("File not linked to session")

        # Remove file from session
        session.files.remove(file_to_remove)

        await db.commit()
        await db.refresh(session)

        return session

    @staticmethod
    async def get_session_files(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID
    ) -> list[File]:
        """Get all files linked to a session.

        Args:
            db: Database session
            session_id: Session UUID
            user_id: User UUID (for ownership check)

        Returns:
            List of File records

        Raises:
            ValueError: If session not found
        """
        # Get session with files eagerly loaded
        session = await ChatSessionService.get_user_session(db, session_id, user_id)

        if session is None:
            raise ValueError("Session not found")

        return session.files

    @staticmethod
    async def generate_session_title(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
    ) -> ChatSession | None:
        """Generate a title for a session using LLM.

        SECURITY: Reads the first user message directly from the database.
        No client-provided text is sent to the LLM -- this prevents the
        endpoint from being used as a general-purpose LLM proxy.

        Only generates if user_modified is False (user hasn't manually renamed).
        Fails silently on LLM errors (leaves title unchanged).
        """
        session = await ChatSessionService.get_user_session(db, session_id, user_id)
        if session is None:
            return None

        # Don't overwrite user-set titles
        if session.user_modified:
            return session

        try:
            from sqlalchemy import select as sa_select
            from app.models.chat_message import ChatMessage
            from app.agents.config import (
                get_agent_provider,
                get_agent_model,
                get_agent_temperature,
                get_agent_max_tokens,
                get_agent_prompt,
                get_api_key_for_provider,
            )
            from app.agents.llm_factory import get_llm, invoke_with_logging, validate_llm_response
            from app.config import get_settings
            from langchain_core.messages import SystemMessage, HumanMessage

            # Read the first user message from the database (not from client)
            msg_result = await db.execute(
                sa_select(ChatMessage.content)
                .where(
                    ChatMessage.session_id == session_id,
                    ChatMessage.user_id == user_id,
                    ChatMessage.role == "user",
                )
                .order_by(ChatMessage.created_at.asc())
                .limit(1)
            )
            first_message = msg_result.scalar_one_or_none()

            if not first_message:
                return session  # No user messages yet -- nothing to generate from

            # Truncate to prevent excessive LLM input (defense in depth)
            user_text = first_message[:500]

            # Load agent config using existing config pattern
            provider = get_agent_provider("title_generator")
            model = get_agent_model("title_generator")
            temperature = get_agent_temperature("title_generator")
            max_tokens = get_agent_max_tokens("title_generator")
            system_prompt = get_agent_prompt("title_generator")
            settings = get_settings()
            api_key = get_api_key_for_provider(provider, settings)

            kwargs = {"max_tokens": max_tokens, "temperature": temperature}
            if provider == "ollama":
                kwargs["base_url"] = settings.ollama_base_url

            llm = get_llm(
                provider=provider,
                model=model,
                api_key=api_key,
                **kwargs,
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_text),
            ]

            response = await invoke_with_logging(
                llm, messages, "title_generator",
                provider, model
            )
            title = validate_llm_response(
                response, provider, model, "title_generator"
            )

            # Clean up: strip quotes, limit to 100 chars
            title = title.strip().strip('"').strip("'")
            if len(title) > 100:
                title = title[:97] + "..."

            session.title = title
            await db.commit()
            await db.refresh(session)
            return session

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Title generation failed for session {session_id}: {e}")
            # Fail silently -- session keeps its current title
            return session
