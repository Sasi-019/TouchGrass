import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

function SignIn() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(event) {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", formData);

      const token = response.data.access_token;

      localStorage.setItem("touchgrass_token", token);

      // New users (no profile yet) go to profile discovery first.
      try {
        await api.get("/profile");
        navigate("/home");
      } catch (profileError) {
        navigate(
          profileError.response?.status === 404
            ? "/profile-discovery"
            : "/home"
        );
      }
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        "Invalid email or password.";

      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#eef6ef] flex items-center justify-center px-4">

      <div className="w-full max-w-md">

        <div className="text-center mb-8">
          <p className="text-sm font-semibold text-[#5c8d68] tracking-wide uppercase">
            TouchGrass
          </p>

          <h1 className="mt-2 text-4xl font-bold text-[#18352a]">
            Welcome back
          </h1>

          <p className="mt-3 text-[#64756b]">
            Ready to spend some time away from the screen?
          </p>
        </div>

        <div className="bg-white rounded-3xl shadow-lg p-8">

          <form onSubmit={handleSubmit} className="space-y-5">

            <div>
              <label className="block text-sm font-medium text-[#30483b] mb-2">
                Email
              </label>

              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                required
                className="w-full rounded-xl border border-[#d5e1d7] px-4 py-3 outline-none focus:border-[#5c8d68] focus:ring-2 focus:ring-[#dcecdf]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#30483b] mb-2">
                Password
              </label>

              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Your password"
                required
                className="w-full rounded-xl border border-[#d5e1d7] px-4 py-3 outline-none focus:border-[#5c8d68] focus:ring-2 focus:ring-[#dcecdf]"
              />
            </div>

            {error && (
              <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-[#3f704d] px-4 py-3 font-semibold text-white transition hover:bg-[#315c3e] disabled:opacity-60"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>

          </form>

          <p className="mt-6 text-center text-sm text-[#64756b]">
            Don't have an account?{" "}
            <Link
              to="/signup"
              className="font-semibold text-[#3f704d] hover:underline"
            >
              Create one
            </Link>
          </p>

        </div>

      </div>

    </div>
  );
}

export default SignIn;