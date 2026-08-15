import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(identifier.trim().toLowerCase(), password);
      navigate("/home");
    } catch (err) {
      setError(err.response?.data?.error || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-full bg-nextweet flex items-center justify-center text-white font-extrabold text-2xl mb-3">
            N
          </div>
          <h1 className="text-2xl font-extrabold text-gray-900">Log in to Nextweet</h1>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="Username or email"
            required
            className="border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-nextweet focus:border-transparent text-sm"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
            className="border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-nextweet focus:border-transparent text-sm"
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="bg-nextweet hover:bg-nextweet-dark disabled:opacity-60 text-white font-bold rounded-full py-3 transition-colors"
          >
            {loading ? "Logging in…" : "Log in"}
          </button>
        </form>

        <p className="text-sm text-gray-500 mt-6 text-center">
          Don't have an account?{" "}
          <Link to="/register" className="text-nextweet font-semibold hover:underline">
            Sign up
          </Link>
        </p>

        <div className="mt-8 bg-gray-50 rounded-xl p-4 text-xs text-gray-500">
          <p className="font-semibold mb-1">Demo accounts (password: password123)</p>
          <p>@nexora · @nikhil · @nandha · @neha · @arjun</p>
        </div>
      </div>
    </div>
  );
}
