import { redirect } from "next/navigation";

/**
 * Root page — redirects to /leads dashboard.
 */
export default function Home() {
  redirect("/leads");
}
