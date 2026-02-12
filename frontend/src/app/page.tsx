import { redirect } from "next/navigation";

/**
 * Root page - redirects to new session page.
 * Auth check happens in dashboard layout.
 */
export default function Home() {
  redirect("/sessions/new");
}
