import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ displayName: "", username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      navigate("/home");
    } catch (err) {
      setError(err.response?.data?.error || "Could not create account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-full bg-nextweet flex items-center justify-center text-white font-extrabold text-2xl mb-3">
            N
          </div>
          <h1 className="text-2xl font-extrabold text-gray-900">Join Nextweet today</h1>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            value={form.displayName}
            onChange={update("displayName")}
            placeholder="Display name"
            required
            className="border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-nextweet focus:border-transparent text-sm"
          />
          <input
            value={form.username}
            onChange={update("username")}
            placeholder="Username (letters, numbers, _)"
            required
            className="border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-nextweet focus:border-transparent text-sm"
          />
          <input
            type="email"
            value={form.email}
            onChange={update("email")}
            placeholder="Email"
            required
            className="border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-nextweet focus:border-transparent text-sm"
          />
          <input
            type="password"
            value={form.password}
            onChange={update("password")}
            placeholder="Password (6+ characters)"
            required
            className="border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-nextweet focus:border-transparent text-sm"
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="bg-nextweet hover:bg-nextweet-dark disabled:opacity-60 text-white font-bold rounded-full py-3 transition-colors"
          >
            {loading ? "Creating account…" : "Sign up"}
          </button>
        </form>

        <p className="text-sm text-gray-500 mt-6 text-center">
          Already have an account?{" "}
          <Link to="/login" className="text-nextweet font-semibold hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
