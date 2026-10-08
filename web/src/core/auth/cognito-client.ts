import { UserManager, type UserManagerSettings } from "oidc-client-ts";
import { env } from "../config/env";

export function createCognitoUserManager(): UserManager | null {
  if (typeof window === "undefined") return null;
  if (!env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || !env.NEXT_PUBLIC_COGNITO_CLIENT_ID) {
    return null;
  }

  const authority = env.NEXT_PUBLIC_COGNITO_DOMAIN
    ? `https://${env.NEXT_PUBLIC_COGNITO_DOMAIN}`
    : `https://cognito-idp.us-east-1.amazonaws.com/${env.NEXT_PUBLIC_COGNITO_USER_POOL_ID}`;

  const settings: UserManagerSettings = {
    authority,
    client_id: env.NEXT_PUBLIC_COGNITO_CLIENT_ID,
    redirect_uri: `${window.location.origin}/auth/callback`,
    response_type: "code",
    scope: "openid email profile",
    post_logout_redirect_uri: `${window.location.origin}/login`,
  };

  return new UserManager(settings);
}
