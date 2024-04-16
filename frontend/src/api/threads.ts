import { Chat } from "../types";

export async function getThread(threadId: string): Promise<Chat | null> {
  try {
    const response = await fetch(`/threads/${threadId}`);
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as Chat;
  } catch (error) {
    console.error("Failed to fetch assistant:", error);
    return null;
  }
}
