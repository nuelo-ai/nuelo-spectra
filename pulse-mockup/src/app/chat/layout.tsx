import { AppShell } from "@/components/layout/app-shell";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell title="Chat">{children}</AppShell>;
}
