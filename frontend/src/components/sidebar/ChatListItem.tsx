"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { MessageSquare, MoreVertical, Pencil, Trash2 } from "lucide-react";
import {
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import {
  useUpdateSession,
  useDeleteSession,
} from "@/hooks/useSessionMutations";
import { useSessionStore } from "@/stores/sessionStore";
import type { ChatSessionResponse } from "@/types/session";

interface ChatListItemProps {
  session: ChatSessionResponse;
  isActive: boolean;
}

/**
 * Individual chat item in the sidebar.
 * Shows title only. Hover reveals three-dot menu with Rename and Delete.
 * Rename is inline editing. Delete opens a confirmation dialog.
 */
export function ChatListItem({ session, isActive }: ChatListItemProps) {
  const router = useRouter();
  const { state } = useSidebar();
  const isExpanded = state === "expanded";

  const updateSession = useUpdateSession();
  const deleteSession = useDeleteSession();
  const currentSessionId = useSessionStore((s) => s.currentSessionId);
  const setCurrentSession = useSessionStore((s) => s.setCurrentSession);

  const [isEditing, setIsEditing] = React.useState(false);
  const [editValue, setEditValue] = React.useState(session.title);
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Focus input when entering edit mode
  React.useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleClick = () => {
    if (!isEditing) {
      setCurrentSession(session.id);
      router.push(`/sessions/${session.id}`);
    }
  };

  const handleStartRename = () => {
    setEditValue(session.title);
    setIsEditing(true);
  };

  const handleSaveRename = async () => {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== session.title) {
      try {
        await updateSession.mutateAsync({
          sessionId: session.id,
          title: trimmed,
        });
      } catch (error) {
        console.error("Failed to rename session:", error);
      }
    }
    setIsEditing(false);
  };

  const handleCancelRename = () => {
    setEditValue(session.title);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSaveRename();
    } else if (e.key === "Escape") {
      e.preventDefault();
      handleCancelRename();
    }
  };

  const handleDelete = async () => {
    try {
      await deleteSession.mutateAsync(session.id);
      // If deleted session was the active one, redirect to new session
      if (currentSessionId === session.id) {
        setCurrentSession(null);
        router.push("/dashboard");
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
    setShowDeleteDialog(false);
  };

  return (
    <>
      <SidebarMenuItem>
        {isEditing ? (
          <div className="px-2 py-1">
            <Input
              ref={inputRef}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleSaveRename}
              className="h-7 text-sm"
              aria-label="Rename chat"
            />
          </div>
        ) : (
          <>
            <SidebarMenuButton
              tooltip={session.title}
              isActive={isActive}
              onClick={handleClick}
            >
              <MessageSquare className="shrink-0" />
              {isExpanded && (
                <span className="truncate">{session.title}</span>
              )}
            </SidebarMenuButton>

            {isExpanded && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuAction showOnHover>
                    <MoreVertical />
                    <span className="sr-only">More options</span>
                  </SidebarMenuAction>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="right" align="start">
                  <DropdownMenuItem onClick={handleStartRename}>
                    <Pencil className="mr-2 h-4 w-4" />
                    Rename
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setShowDeleteDialog(true)}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </>
        )}
      </SidebarMenuItem>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this chat?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{session.title}&quot; and all
              its messages. Linked files will not be affected.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              variant="destructive"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
