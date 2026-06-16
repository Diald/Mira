import { Navigate, Route, Routes } from "react-router-dom";
import { tokenStore } from "./api/client.js";
import Chat from "./pages/Chat.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";

function RequireAuth({ children }) {
  return tokenStore.get() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Home />
          </RequireAuth>
        }
      />
      <Route
        path="/notebook/:id"
        element={
          <RequireAuth>
            <Chat />
          </RequireAuth>
        }
      />
    </Routes>
  );
}
