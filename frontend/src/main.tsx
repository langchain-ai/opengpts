import ReactDOM from "react-dom/client";
import { v4 as uuidv4 } from "uuid";
import App from "./App.tsx";
import "./index.css";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { StrictMode } from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { NotFound } from "./components/NotFound.tsx";

function getCookie(name: string) {
  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));
  return cookie ? cookie.split("=")[1] : null;
}

document.addEventListener("DOMContentLoaded", () => {
  const userId =
    localStorage.getItem("opengpts_user_id") ||
    getCookie("opengpts_user_id") ||
    uuidv4();

  // Push the user id to localStorage in any case to make it stable
  localStorage.setItem("opengpts_user_id", userId);
  // Ensure the cookie is always set (for both new and returning users)
  const weekInMilliseconds = 7 * 24 * 60 * 60 * 1000;
  const expires = new Date(Date.now() + weekInMilliseconds).toUTCString();
  document.cookie = `opengpts_user_id=${userId}; path=/; expires=${expires}; SameSite=Lax;`;
});

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/thread/:chatId" element={<App />} />
          <Route
            path="/assistant/:assistantId/edit"
            element={<App edit={true} />}
          />
          <Route path="/assistant/:assistantId" element={<App />} />
          <Route path="/" element={<App />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
