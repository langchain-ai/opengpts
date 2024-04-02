import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
// import LoginPage from "./pages/LoginPage";
// import RegisterPage from "./pages/RegisterPage";
import Home from "./components/Home";
import LoginSignUp from "./components/LoginSignUp";

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route
          path="/home"
          element={
              <Home />
          }
        />
        <Route path="/" element={<LoginSignUp />} />
        {/* <Route path="/register" element={<RegisterPage />} /> */}
      </Routes>
    </Router>
  );
};

export default App;
