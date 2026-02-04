import { redirect } from "next/navigation";

/**
 * Root page - redirects to login.
 * Users will be redirected to dashboard after authentication.
 */
export default function Home() {
  redirect("/login");
}
