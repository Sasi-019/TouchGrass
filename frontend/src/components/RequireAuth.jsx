import { Navigate, useLocation } from "react-router-dom";

/**
 * Sends signed-out visitors to /signin.
 * (A stale or expired token is also cleared automatically by the API layer
 * the first time the backend answers 401.)
 */
export default function RequireAuth({ children }) {
  const location = useLocation();

  let token = null;

  try {
    token = localStorage.getItem("touchgrass_token");
  } catch {
    token = null;
  }

  if (!token) {
    return <Navigate to="/signin" replace state={{ from: location }} />;
  }

  return children;
}
