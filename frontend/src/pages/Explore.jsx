import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Search as SearchIcon } from "lucide-react";
import TweetCard from "../components/TweetCard";
import Avatar from "../components/Avatar";
import api from "../api/client";
import { useNavigate } from "react-router-dom";

export default function Explore() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQ = searchParams.get("q") || "";
  const [query, setQuery] = useState(initialQ);
  const [tweets, setTweets] = useState([]);
  const [users, setUsers] = useState([]);
  const [tab, setTab] = useState("tweets");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const loadExplore = useCallback(async () => {
    setLoading(true);
    const res = await api.get("/tweets/explore");
    setTweets(res.data);
    setLoading(false);
  }, []);

  const runSearch = useCallback(async (q) => {
    setLoading(true);
    const [tRes, uRes] = await Promise.all([
      api.get("/tweets/search", { params: { q } }),
      api.get("/users/search", { params: { q: q.replace("#", "") } }),
    ]);
    setTweets(tRes.data);
    setUsers(uRes.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    const q = searchParams.get("q") || "";
    setQuery(q);
    if (q) runSearch(q);
    else loadExplore();
  }, [searchParams, runSearch, loadExplore]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSearchParams(query.trim() ? { q: query.trim() } : {});
  };

  const handleUpdate = (updated) => {
    setTweets((prev) => prev.map((t) => (t.id === updated.id ? { ...t, ...updated } : t)));
  };
  const handleDelete = (id) => setTweets((prev) => prev.filter((t) => t.id !== id));

  return (
    <div>
      <div className="sticky top-0 bg-white/90 backdrop-blur z-10 border-b border-gray-100 px-4 py-3">
        <form onSubmit={handleSubmit} className="relative">
          <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search Nextweet"
            className="w-full bg-gray-100 focus:bg-white focus:ring-2 focus:ring-nextweet rounded-full py-2.5 pl-11 pr-4 text-sm outline-none transition-all"
          />
        </form>

        {searchParams.get("q") && (
          <div className="flex gap-6 mt-3 border-b border-gray-100 -mx-4 px-4">
            {["tweets", "people"].map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`pb-3 text-sm font-semibold capitalize border-b-2 ${
                  tab === t ? "border-nextweet text-gray-900" : "border-transparent text-gray-500"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        )}
      </div>

      {!searchParams.get("q") && (
        <div className="px-4 py-3 border-b border-gray-100">
          <h2 className="font-extrabold text-lg text-gray-900">What's happening</h2>
        </div>
      )}

      {loading && <div className="p-6 text-center text-gray-400 text-sm">Loading…</div>}

      {!loading && searchParams.get("q") && tab === "people" && (
        <div>
          {users.length === 0 && (
            <p className="p-6 text-center text-gray-400 text-sm">No users found.</p>
          )}
          {users.map((u) => (
            <div
              key={u.id}
              onClick={() => navigate(`/profile/${u.username}`)}
              className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
            >
              <Avatar user={u} size={44} />
              <div className="min-w-0">
                <p className="font-bold text-sm text-gray-900 truncate">{u.displayName}</p>
                <p className="text-sm text-gray-500 truncate">@{u.username}</p>
                {u.bio && <p className="text-sm text-gray-600 mt-0.5 line-clamp-1">{u.bio}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && (!searchParams.get("q") || tab === "tweets") && (
        <div>
          {tweets.length === 0 && (
            <p className="p-6 text-center text-gray-400 text-sm">No tweets found.</p>
          )}
          {tweets.map((t) => (
            <TweetCard key={t.id} tweet={t} onUpdate={handleUpdate} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
