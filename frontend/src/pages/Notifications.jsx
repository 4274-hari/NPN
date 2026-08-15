import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Heart, MessageCircle, Repeat2, UserPlus, AtSign, Bell } from "lucide-react";
import Avatar from "../components/Avatar";
import api from "../api/client";

const ICONS = {
  like: { icon: Heart, color: "text-pink-500" },
  comment: { icon: MessageCircle, color: "text-nextweet" },
  retweet: { icon: Repeat2, color: "text-green-600" },
  follow: { icon: UserPlus, color: "text-nextweet" },
  mention: { icon: AtSign, color: "text-nextweet" },
};

const VERBS = {
  like: "liked your tweet",
  comment: "replied to your tweet",
  retweet: "reposted your tweet",
  follow: "followed you",
  mention: "mentioned you in a tweet",
};

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    const res = await api.get("/notifications");
    setItems(res.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    api.post("/notifications/read-all");
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  return (
    <div>
      <div className="sticky top-0 bg-white/90 backdrop-blur z-10 border-b border-gray-100 px-4 py-3">
        <h1 className="text-xl font-extrabold text-gray-900">Notifications</h1>
      </div>

      {loading && <div className="p-6 text-center text-gray-400 text-sm">Loading…</div>}

      {!loading && items.length === 0 && (
        <div className="flex flex-col items-center text-center px-8 py-16 text-gray-500">
          <Bell className="mb-3 text-nextweet" size={32} />
          <p className="font-bold text-lg text-gray-900 mb-1">Nothing here yet</p>
          <p className="text-sm">When someone interacts with your tweets, you'll see it here.</p>
        </div>
      )}

      {items.map((n) => {
        const meta = ICONS[n.type] || ICONS.mention;
        const Icon = meta.icon;
        return (
          <div
            key={n.id}
            onClick={() => (n.tweetId ? navigate(`/tweet/${n.tweetId}`) : navigate(`/profile/${n.actor?.username}`))}
            className={`flex gap-3 px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
              !n.isRead ? "bg-nextweet/5" : ""
            }`}
          >
            <Icon className={meta.color} size={22} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <Avatar user={n.actor} size={28} />
                <p className="text-sm text-gray-900">
                  <span className="font-bold">{n.actor?.displayName}</span>{" "}
                  <span className="text-gray-600">{VERBS[n.type] || "interacted with you"}</span>
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
