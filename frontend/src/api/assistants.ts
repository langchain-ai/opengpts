import { Config } from "../hooks/useConfigList";

export async function getAssistant(
  assistantId: string,
): Promise<Config | null> {
  console.log("HERE", assistantId)
  try {
    let response = await fetch(`/assistants/${assistantId}`);
    if (!response.ok) {
      // If the first request fails, try the public assistant endpoint
      response = await fetch(`/assistants/public/?shared_id=${assistantId}`);
      if (!response.ok) {
        return null;
      }
    }

    return (await response.json()) as Config;
  } catch (error) {
    console.error("Failed to fetch assistant:", error);
    return null;
  }
}
