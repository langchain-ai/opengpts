import ReactDOM from "react-dom/client";
import { v4 as uuidv4 } from "uuid";
import App from "./App.tsx";
import "./index.css";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { StrictMode } from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { NotFound } from "./components/NotFound.tsx";

if (document.cookie.indexOf("user_id") === -1) {
  document.cookie = `opengpts_user_id=${uuidv4()}; path=/; SameSite=Lax`;
}

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
