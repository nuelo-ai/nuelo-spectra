import { redirect } from "next/navigation";

/**
 * Root page - redirects to dashboard.
 * Auth check happens in dashboard layout.
 */
export default function Home() {
  redirect("/dashboard");
}
