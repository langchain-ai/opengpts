import { useQuery, useQueryClient } from "react-query";
import { useParams } from "react-router-dom";
import { getAssistant } from "../api/assistants";
import { getThread } from "../api/threads";

export function useThreadAndAssistant() {
  // Extract route parameters
  const { chatId, assistantId } = useParams();
  const queryClient = useQueryClient();

  // React Query to fetch chat details if chatId is present
  const { data: currentChat, isLoading: isLoadingChat } = useQuery(
    ["thread", chatId],
    () => getThread(chatId as string),
    {
      enabled: !!chatId,
    },
  );

  // Determine the assistantId to use: either from the chat or the route directly
  const effectiveAssistantId = assistantId || currentChat?.assistant_id;

  // React Query to fetch assistant configuration based on the effectiveAssistantId
  const { data: assistantConfig, isLoading: isLoadingAssistant } = useQuery(
    ["assistant", effectiveAssistantId],
    () => getAssistant(effectiveAssistantId as string),
    {
      enabled: !!effectiveAssistantId,
    },
  );

  const invalidateChat = (chatId: string) => {
    queryClient.invalidateQueries(["thread", chatId]);
  };

  // Return both loading states, the chat data, and the assistant configuration
  return {
    currentChat,
    assistantConfig,
    isLoading: isLoadingChat || isLoadingAssistant,
    invalidateChat,
  };
}
