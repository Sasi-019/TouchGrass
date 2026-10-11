
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
<<<<<<< HEAD
import RequireAuth from "./components/RequireAuth";
=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


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

<<<<<<< HEAD
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
=======
      {/* Profile discovery */}
      <Route
        path="/profile"
        element={<ProfileDiscovery />}
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
      />

      {/* Actual profile dashboard */}
      <Route
        path="/my-profile"
<<<<<<< HEAD
        element={
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        }
=======
        element={<ProfilePage />}
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
      />

      {/* Home */}
      <Route
        path="/home"
<<<<<<< HEAD
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
=======
        element={<HomePage />}
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
      />

      {/* Activity */}
      <Route
        path="/activity/:id"
<<<<<<< HEAD
        element={
          <RequireAuth>
            <Activity />
          </RequireAuth>
        }
=======
        element={<Activity />}
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
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
