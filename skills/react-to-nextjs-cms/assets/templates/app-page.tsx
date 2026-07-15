import client from "@/tina/__generated__/client";
import HomeView from "./home-view";

// Editable route: don't serve a stale cache, or edits look like they didn't save.
export const revalidate = 0;

export default async function Page() {
  // Server-side fetch via the generated typed client. Pass the WHOLE result
  // ({ data, query, variables }) into the client view so useTina can go live.
  const res = await client.queries.page({ relativePath: "home.json" });
  return <HomeView {...res} />;
}
