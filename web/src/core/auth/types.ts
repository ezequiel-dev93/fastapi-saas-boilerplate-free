export interface AuthUser {
  id?: number;
  email: string;
  first_name?: string;
  last_name?: string;
  cognito_sub?: string;
}

export type AuthMode = "dev" | "cognito";

export interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  authMode: AuthMode;
  loginWithDevToken: (email: string) => Promise<void>;
  loginWithCognito: () => Promise<void>;
  logout: () => void;
}
