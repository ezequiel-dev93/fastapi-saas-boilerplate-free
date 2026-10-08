import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "./schema";
import { env } from "../config/env";
import { parseHttpError } from "./errors";

let authTokenGetter: () => string | null = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("saas_access_token");
  }
  return null;
};

let activeOrgIdGetter: () => number | null = () => {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("saas_active_org_id");
    return stored ? Number(stored) : null;
  }
  return null;
};

export function setTokenProvider(getter: () => string | null) {
  authTokenGetter = getter;
}

export function setActiveOrgProvider(getter: () => number | null) {
  activeOrgIdGetter = getter;
}

const authAndOrgMiddleware: Middleware = {
  async onRequest({ request }) {
    const token = authTokenGetter();
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }

    const orgId = activeOrgIdGetter();
    if (orgId) {
      request.headers.set("X-Organization-ID", String(orgId));
    }

    // Set correlation ID if not set
    if (!request.headers.has("X-Request-ID")) {
      const requestId = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2);
      request.headers.set("X-Request-ID", requestId);
    }

    return request;
  },

  async onResponse({ response }) {
    if (!response.ok) {
      let data: unknown;
      try {
        data = await response.clone().json();
      } catch {
        data = await response.clone().text();
      }
      throw parseHttpError(response.status, data, response.statusText);
    }
    return response;
  },
};

export const apiClient = createClient<paths>({
  baseUrl: env.NEXT_PUBLIC_API_URL,
});

apiClient.use(authAndOrgMiddleware);
