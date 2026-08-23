import { apiPost } from "./client";
import type { ChatResponse } from "./types";

export function sendChat(message: string, sessionId?: string): Promise<ChatResponse> {
  return apiPost<ChatResponse>("/chat", {
    message,
    session_id: sessionId ?? null,
  });
}
