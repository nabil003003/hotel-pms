import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { COOKIE_ACCESS_TOKEN } from "@/lib/auth/constants";

export default async function Home() {
  const cookieStore = await cookies();
  const hasToken = Boolean(cookieStore.get(COOKIE_ACCESS_TOKEN)?.value);
  redirect(hasToken ? "/housekeeping" : "/login");
}
