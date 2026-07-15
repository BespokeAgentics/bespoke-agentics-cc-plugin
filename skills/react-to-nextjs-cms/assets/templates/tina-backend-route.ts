import { TinaNodeBackend, LocalBackendAuthProvider } from "@tinacms/datalayer";
import { TinaAuthJSOptions, AuthJsBackendAuthProvider } from "tinacms-authjs";

import databaseClient from "../../../tina/__generated__/databaseClient";

// Tina's backend is a Node (req,res) handler, so this lives under pages/api/ EVEN in an
// App-Router app (pages/api/* and app/* coexist). This one catch-all serves the GraphQL
// content API (/api/tina/gql) and auth (/api/tina/auth/*). Do NOT set runtime = "edge".
const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === "true";

const handler = TinaNodeBackend({
  authProvider: isLocal
    ? LocalBackendAuthProvider()
    : AuthJsBackendAuthProvider({
        authOptions: TinaAuthJSOptions({
          databaseClient,
          secret: process.env.NEXTAUTH_SECRET as string,
        }),
      }),
  databaseClient,
});

export default (req: any, res: any) => {
  return handler(req, res);
};
