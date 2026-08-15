import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import TweetCard from "../components/TweetCard";
import TweetComposer from "../components/TweetComposer";
import api from "../api/client";

export default function TweetDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tweet, setTweet] = useState(null);
  const [replies, setReplies] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.get(`/tweets/${id}`);
    const { replies: r, ...rest } = res.data;
    setTweet(rest);
    setReplies(r);
    setLoading(false);
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleReply = async (content) => {
    await api.post("/tweets", { content, parentId: Number(id) });
    load();
  };

  const handleUpdate = (updated) => setTweet((t) => ({ ...t, ...updated }));
  const handleReplyUpdate = (updated) =>
    setReplies((prev) => prev.map((r) => (r.id === updated.id ? { ...r, ...updated } : r)));
  const handleReplyDelete = (rid) => setReplies((prev) => prev.filter((r) => r.id !== rid));

  const handleDelete = () => navigate(-1);

  if (loading || !tweet) {
    return <div className="p-6 text-center text-gray-400 text-sm">Loading tweet…</div>;
  }

  return (
    <div>
      <div className="sticky top-0 bg-white/90 backdrop-blur z-10 border-b border-gray-100 px-4 py-3 flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="p-2 rounded-full hover:bg-gray-100">
          <ArrowLeft size={18} />
        </button>
        <h1 className="font-extrabold text-lg text-gray-900">Tweet</h1>
      </div>

      <TweetCard tweet={tweet} onUpdate={handleUpdate} onDelete={handleDelete} />

      <TweetComposer
        onSubmit={handleReply}
        placeholder="Tweet your reply"
        buttonLabel="Reply"
        compact
      />

      <div>
        {replies.length === 0 ? (
          <p className="p-6 text-center text-gray-400 text-sm">No replies yet. Be the first to reply!</p>
        ) : (
          replies.map((r) => (
            <TweetCard key={r.id} tweet={r} onUpdate={handleReplyUpdate} onDelete={handleReplyDelete} />
          ))
        )}
      </div>
    </div>
  );
}
