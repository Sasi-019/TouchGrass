
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

      {/* Profile discovery */}
      <Route
        path="/profile"
        element={<ProfileDiscovery />}
      />

      {/* Actual profile dashboard */}
      <Route
        path="/my-profile"
        element={<ProfilePage />}
      />

      {/* Home */}
      <Route
        path="/home"
        element={<HomePage />}
      />

      {/* Activity */}
      <Route
        path="/activity/:id"
        element={<Activity />}
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
