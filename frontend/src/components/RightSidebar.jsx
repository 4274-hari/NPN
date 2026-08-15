import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import Avatar from "./Avatar";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function RightSidebar() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [trending, setTrending] = useState([]);
  const [suggested, setSuggested] = useState([]);

  useEffect(() => {
    api.get("/tweets/trending").then((res) => setTrending(res.data));
    api.get("/users/suggested").then((res) => setSuggested(res.data));
  }, []);

  const handleFollow = async (target) => {
    setSuggested((prev) =>
      prev.map((u) => (u.id === target.id ? { ...u, isFollowedByMe: true } : u))
    );
    try {
      await api.post(`/users/${target.username}/follow`);
    } catch {
      // ignore
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) navigate(`/explore?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <aside className="hidden lg:flex flex-col gap-4 w-[320px] flex-shrink-0 py-3 px-4 sticky top-0 h-screen overflow-y-auto no-scrollbar">
      <form onSubmit={handleSearch} className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search Nextweet"
          className="w-full bg-gray-100 focus:bg-white focus:ring-2 focus:ring-nextweet rounded-full py-2.5 pl-11 pr-4 text-sm outline-none transition-all border border-transparent focus:border-nextweet/30"
        />
      </form>

      <div className="bg-gray-50 rounded-2xl overflow-hidden">
        <h2 className="font-extrabold text-lg text-gray-900 px-4 pt-3 pb-1">Trends for you</h2>
        {trending.map((t) => (
          <button
            key={t.tag}
            onClick={() => navigate(`/explore?q=${encodeURIComponent("#" + t.tag)}`)}
            className="w-full text-left px-4 py-2.5 hover:bg-gray-100 transition-colors block"
          >
            <p className="text-xs text-gray-500">Trending{t.count > 0 ? ` · ${t.count} tweets` : ""}</p>
            <p className="font-bold text-[15px] text-gray-900">#{t.tag}</p>
          </button>
        ))}
        {trending.length === 0 && (
          <p className="px-4 pb-3 text-sm text-gray-400">No trends yet — start tweeting with #hashtags!</p>
        )}
      </div>

      <div className="bg-gray-50 rounded-2xl overflow-hidden pb-2">
        <h2 className="font-extrabold text-lg text-gray-900 px-4 pt-3 pb-1">Who to follow</h2>
        {suggested
          .filter((u) => u.id !== user?.id)
          .map((u) => (
            <div key={u.id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-100 transition-colors">
              <button onClick={() => navigate(`/profile/${u.username}`)}>
                <Avatar user={u} size={40} />
              </button>
              <div className="min-w-0 flex-1">
                <button
                  onClick={() => navigate(`/profile/${u.username}`)}
                  className="font-bold text-sm text-gray-900 hover:underline truncate block"
                >
                  {u.displayName}
                </button>
                <p className="text-sm text-gray-500 truncate">@{u.username}</p>
              </div>
              {!u.isFollowedByMe ? (
                <button
                  onClick={() => handleFollow(u)}
                  className="bg-gray-900 hover:bg-black text-white text-sm font-bold rounded-full px-4 py-1.5 flex-shrink-0"
                >
                  Follow
                </button>
              ) : (
                <span className="text-sm text-gray-400 flex-shrink-0">Following</span>
              )}
            </div>
          ))}
        {suggested.length === 0 && (
          <p className="px-4 pb-2 text-sm text-gray-400">No suggestions right now.</p>
        )}
      </div>

      <p className="text-xs text-gray-400 px-4">Nextweet · A place to talk, built for your feed.</p>
    </aside>
  );
}
