import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Avatar from "../components/Avatar";
import api from "../api/client";

export default function FollowList({ mode }) {
  const { username } = useParams();
  const navigate = useNavigate();
  const [people, setPeople] = useState([]);

  useEffect(() => {
    api.get(`/users/${username}/${mode}`).then((res) => setPeople(res.data));
  }, [username, mode]);

  const handleFollow = async (target) => {
    setPeople((prev) =>
      prev.map((u) => (u.id === target.id ? { ...u, isFollowedByMe: !u.isFollowedByMe } : u))
    );
    const endpoint = target.isFollowedByMe ? "unfollow" : "follow";
    await api.post(`/users/${target.username}/${endpoint}`);
  };

  return (
    <div>
      <div className="sticky top-0 bg-white/90 backdrop-blur z-10 border-b border-gray-100 px-4 py-3 flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="p-2 rounded-full hover:bg-gray-100">
          <ArrowLeft size={18} />
        </button>
        <h1 className="font-extrabold text-lg text-gray-900 capitalize">{mode}</h1>
      </div>
      {people.length === 0 && <p className="p-6 text-center text-gray-400 text-sm">Nobody here yet.</p>}
      {people.map((u) => (
        <div key={u.id} className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 hover:bg-gray-50">
          <button onClick={() => navigate(`/profile/${u.username}`)}>
            <Avatar user={u} size={44} />
          </button>
          <div className="min-w-0 flex-1">
            <button
              onClick={() => navigate(`/profile/${u.username}`)}
              className="font-bold text-sm text-gray-900 hover:underline block truncate"
            >
              {u.displayName}
            </button>
            <p className="text-sm text-gray-500 truncate">@{u.username}</p>
          </div>
          {!u.isMe && (
            <button
              onClick={() => handleFollow(u)}
              className={`text-sm font-bold rounded-full px-4 py-1.5 flex-shrink-0 ${
                u.isFollowedByMe
                  ? "border border-gray-300 hover:bg-red-50 hover:text-red-600 hover:border-red-300"
                  : "bg-gray-900 hover:bg-black text-white"
              }`}
            >
              {u.isFollowedByMe ? "Following" : "Follow"}
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
