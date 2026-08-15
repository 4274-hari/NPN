import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Calendar, MapPin } from "lucide-react";
import Avatar from "../components/Avatar";
import TweetCard from "../components/TweetCard";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

export default function Profile() {
  const { username } = useParams();
  const { user: me, setUser: setMe } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [tweets, setTweets] = useState([]);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ displayName: "", bio: "", location: "" });

  const load = useCallback(async () => {
    const [pRes, tRes] = await Promise.all([
      api.get(`/users/${username}`),
      api.get(`/tweets/user/${username}`),
    ]);
    setProfile(pRes.data);
    setTweets(tRes.data);
    setForm({
      displayName: pRes.data.displayName,
      bio: pRes.data.bio || "",
      location: pRes.data.location || "",
    });
  }, [username]);

  useEffect(() => {
    load();
  }, [load]);

  const handleFollowToggle = async () => {
    if (!profile) return;
    const endpoint = profile.isFollowedByMe ? "unfollow" : "follow";
    const res = await api.post(`/users/${profile.username}/${endpoint}`);
    setProfile((p) => ({ ...p, isFollowedByMe: !p.isFollowedByMe, followersCount: res.data.followersCount }));
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    const res = await api.put("/users/me", form);
    setProfile(res.data);
    setMe(res.data);
    localStorage.setItem("nextweet_user", JSON.stringify(res.data));
    setEditing(false);
  };

  const handleUpdate = (updated) =>
    setTweets((prev) => prev.map((t) => (t.id === updated.id ? { ...t, ...updated } : t)));
  const handleDelete = (id) => setTweets((prev) => prev.filter((t) => t.id !== id));

  if (!profile) return <div className="p-6 text-center text-gray-400 text-sm">Loading profile…</div>;

  return (
    <div>
      <div className="sticky top-0 bg-white/90 backdrop-blur z-10 border-b border-gray-100 px-4 py-3 flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="p-2 rounded-full hover:bg-gray-100">
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="font-extrabold text-lg text-gray-900 leading-tight">{profile.displayName}</h1>
          <p className="text-xs text-gray-500">{profile.tweetsCount} tweets</p>
        </div>
      </div>

      <div className="h-32 sm:h-40 bg-gradient-to-r from-nextweet to-nextweet-light" />

      <div className="px-4">
        <div className="flex justify-between items-end -mt-12">
          <Avatar user={profile} size={90} className="ring-4 ring-white" />
          {profile.isMe ? (
            <button
              onClick={() => setEditing((v) => !v)}
              className="mt-14 border border-gray-300 hover:bg-gray-100 font-bold text-sm rounded-full px-4 py-2"
            >
              Edit profile
            </button>
          ) : (
            <button
              onClick={handleFollowToggle}
              className={`mt-14 font-bold text-sm rounded-full px-4 py-2 ${
                profile.isFollowedByMe
                  ? "border border-gray-300 hover:border-red-300 hover:bg-red-50 hover:text-red-600 text-gray-900"
                  : "bg-gray-900 hover:bg-black text-white"
              }`}
            >
              {profile.isFollowedByMe ? "Following" : "Follow"}
            </button>
          )}
        </div>

        {editing ? (
          <form onSubmit={handleSaveProfile} className="mt-4 flex flex-col gap-3 pb-4">
            <input
              value={form.displayName}
              onChange={(e) => setForm((f) => ({ ...f, displayName: e.target.value }))}
              placeholder="Display name"
              className="border border-gray-300 rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-nextweet"
            />
            <textarea
              value={form.bio}
              onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
              placeholder="Bio"
              maxLength={280}
              rows={3}
              className="border border-gray-300 rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-nextweet resize-none"
            />
            <input
              value={form.location}
              onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
              placeholder="Location"
              className="border border-gray-300 rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-nextweet"
            />
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="text-sm font-semibold px-4 py-2 rounded-full hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-nextweet hover:bg-nextweet-dark text-white text-sm font-bold px-4 py-2 rounded-full"
              >
                Save
              </button>
            </div>
          </form>
        ) : (
          <div className="mt-3 pb-4">
            <h2 className="font-extrabold text-xl text-gray-900">{profile.displayName}</h2>
            <p className="text-gray-500 text-sm">@{profile.username}</p>
            {profile.bio && <p className="text-gray-900 text-sm mt-3">{profile.bio}</p>}
            <div className="flex items-center gap-4 text-gray-500 text-sm mt-3">
              {profile.location && (
                <span className="flex items-center gap-1">
                  <MapPin size={14} /> {profile.location}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Calendar size={14} /> Joined{" "}
                {new Date(profile.createdAt).toLocaleDateString(undefined, {
                  month: "long",
                  year: "numeric",
                })}
              </span>
            </div>
            <div className="flex gap-4 text-sm mt-3">
              <button
                onClick={() => navigate(`/profile/${profile.username}/following`)}
                className="hover:underline"
              >
                <span className="font-bold text-gray-900">{profile.followingCount}</span>{" "}
                <span className="text-gray-500">Following</span>
              </button>
              <button
                onClick={() => navigate(`/profile/${profile.username}/followers`)}
                className="hover:underline"
              >
                <span className="font-bold text-gray-900">{profile.followersCount}</span>{" "}
                <span className="text-gray-500">Followers</span>
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-100">
        {tweets.length === 0 ? (
          <p className="p-6 text-center text-gray-400 text-sm">No tweets yet.</p>
        ) : (
          tweets.map((t) => (
            <TweetCard key={t.id} tweet={t} onUpdate={handleUpdate} onDelete={handleDelete} />
          ))
        )}
      </div>
    </div>
  );
}
