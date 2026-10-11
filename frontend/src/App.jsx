import {
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";

import Landing from "./pages/Landing";
import SignUp from "./pages/SignUp";
import SignIn from "./pages/SignIn";
import ProfileDiscovery from "./pages/ProfileDiscovery";
import Profile from "./pages/Profile";
import Home from "./pages/Home";
import Activity from "./pages/Activity";
import RequireAuth from "./components/RequireAuth";


function HomePage() {
  const navigate = useNavigate();

  return (
    <Home
      onProfile={() => navigate("/my-profile")}
    />
  );
}


function ProfilePage() {
  const navigate = useNavigate();

  return (
    <Profile
      onBack={() => navigate("/home")}
    />
  );
}


export default function App() {
  return (
    <Routes>

      {/* Landing */}
      <Route
        path="/"
        element={<Landing />}
      />

      {/* Authentication */}
      <Route
        path="/signup"
        element={<SignUp />}
      />

      <Route
        path="/signin"
        element={<SignIn />}
      />

      {/* Profile discovery ("/profile" is kept for backward compatibility) */}
      <Route
        path="/profile-discovery"
        element={
          <RequireAuth>
            <ProfileDiscovery />
          </RequireAuth>
        }
      />

      <Route
        path="/profile"
        element={
          <RequireAuth>
            <ProfileDiscovery />
          </RequireAuth>
        }
      />

      {/* Actual profile dashboard */}
      <Route
        path="/my-profile"
        element={
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        }
      />

      {/* Home */}
      <Route
        path="/home"
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
      />

      {/* Activity */}
      <Route
        path="/activity/:id"
        element={
          <RequireAuth>
            <Activity />
          </RequireAuth>
        }
      />

      {/* Unknown routes */}
      <Route
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />

    </Routes>
  );
}