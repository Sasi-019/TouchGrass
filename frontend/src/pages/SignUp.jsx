import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

function SignUp() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
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
      await api.post("/auth/register", formData);

<<<<<<< HEAD
      // Sign the new user straight in so they land on profile discovery
      // (Sign Up -> Profile Discovery) instead of a second login screen.
      try {
        const login = await api.post("/auth/login", {
          email: formData.email,
          password: formData.password,
        });

        localStorage.setItem(
          "touchgrass_token",
          login.data.access_token
        );

        navigate("/profile-discovery");
      } catch {
        // Account exists; fall back to the normal sign-in page.
        navigate("/signin");
      }
=======
      alert("Account created successfully!");

      navigate("/signin");
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        "Something went wrong. Please try again.";

      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#eef6ef] flex items-center justify-center px-4">

      <div className="w-full max-w-md">

        {/* Heading */}
        <div className="text-center mb-8">
          <p className="text-sm font-semibold text-[#5c8d68] tracking-wide uppercase">
            TouchGrass
          </p>

          <h1 className="mt-2 text-4xl font-bold text-[#18352a]">
            Create your account
          </h1>

          <p className="mt-3 text-[#64756b]">
            Start discovering things worth doing offline.
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-3xl shadow-lg p-8">

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-[#30483b] mb-2">
                Name
              </label>

              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Your name"
                required
                className="w-full rounded-xl border border-[#d5e1d7] px-4 py-3 outline-none focus:border-[#5c8d68] focus:ring-2 focus:ring-[#dcecdf]"
              />
            </div>

            {/* Email */}
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

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-[#30483b] mb-2">
                Password
              </label>

              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Create a password"
                required
                className="w-full rounded-xl border border-[#d5e1d7] px-4 py-3 outline-none focus:border-[#5c8d68] focus:ring-2 focus:ring-[#dcecdf]"
              />
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-[#3f704d] px-4 py-3 font-semibold text-white transition hover:bg-[#315c3e] disabled:opacity-60"
            >
              {loading ? "Creating account..." : "Create account"}
            </button>

          </form>

          {/* Sign in */}
          <p className="mt-6 text-center text-sm text-[#64756b]">
            Already have an account?{" "}
            <Link
              to="/signin"
              className="font-semibold text-[#3f704d] hover:underline"
            >
              Sign in
            </Link>
          </p>

        </div>

      </div>

    </div>
  );
}

export default SignUp;