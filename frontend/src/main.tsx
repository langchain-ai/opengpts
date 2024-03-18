import ReactDOM from "react-dom/client";
import { v4 as uuidv4 } from "uuid";
import App from "./App.tsx";
import "./index.css";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { StrictMode } from "react";

if (document.cookie.indexOf("user_id") === -1) {
  document.cookie = `opengpts_user_id=${uuidv4()}; path=/; SameSite=Lax`;
}

const router = createBrowserRouter([
  {
    path: "*",
    element: <App />,
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
