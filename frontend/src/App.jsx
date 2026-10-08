
import { Routes, Route, Navigate } from "react-router-dom";

import Landing from "./pages/Landing";
import SignUp from "./pages/SignUp";
import SignIn from "./pages/SignIn";
import ProfileDiscovery from "./pages/ProfileDiscovery";
import Profile from "./pages/Profile";
import Home from "./pages/Home";
import Activity from "./pages/Activity";


function HomePage() {

  const navigate =
    useNavigate();

  return (
    <Home
      onProfile={() =>
        navigate("/profile")
      }
    />
  );
}


function ProfilePage() {

  const navigate =
    useNavigate();

  return (
    <Profile
      onBack={() =>
        navigate("/home")
      }
    />
  );
}


export default function App() {

  return (
  <Routes>
    <Route path="/" element={<Landing />} />
    <Route path="/signup" element={<SignUp />} />
    <Route path="/signin" element={<SignIn />} />
    <Route path="/profile" element={<ProfileDiscovery />} />
    <Route path="/my-profile" element={<Profile />} />
    <Route path="/home" element={<Home />} />
    <Route path="/activity/:id" element={<Activity />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);
}