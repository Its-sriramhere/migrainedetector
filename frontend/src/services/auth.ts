import type { LoginRequest, RegisterRequest, TokenResponse } from "../types";
import { api } from "./api";

export function storeToken(token: string): void {
  localStorage.setItem("mg_token", token);
}

export function getToken(): string | null {
  return localStorage.getItem("mg_token");
}

export function clearToken(): void {
  localStorage.removeItem("mg_token");
}

export async function login(body: LoginRequest): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>("/api/auth/login", body);
  storeToken(response.access_token);
  return response;
}

export async function register(body: RegisterRequest): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>("/api/auth/register", body);
  storeToken(response.access_token);
  return response;
}

export async function logout(): Promise<void> {
  try {
    await api.post("/api/auth/logout");
  } finally {
    clearToken();
  }
}