import { useEffect, useState, useCallback } from "react";
import { Sparkles } from "lucide-react";
import TweetComposer from "../components/TweetComposer";
import TweetCard from "../components/TweetCard";
import api from "../api/client";

export default function Home() {
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const res = await api.get("/tweets/feed");
    setTweets(res.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000); // polling for new activity
    return () => clearInterval(interval);
  }, [load]);

  const handleCreate = async (content) => {
    const res = await api.post("/tweets", { content });
    setTweets((prev) => [res.data, ...prev]);
  };

  const handleUpdate = (updated) => {
    setTweets((prev) =>
      prev.map((t) =>
        t.id === updated.id || t.originalTweetId === updated.id ? { ...t, ...updated, id: t.id, isRetweet: t.isRetweet, retweetedBy: t.retweetedBy, originalTweetId: t.originalTweetId } : t
      )
    );
  };

  const handleDelete = (id) => setTweets((prev) => prev.filter((t) => t.id !== id));

  return (
    <div>
      <div className="sticky top-0 bg-white/90 backdrop-blur z-10 border-b border-gray-100 px-4 py-3">
        <h1 className="text-xl font-extrabold text-gray-900">Home</h1>
      </div>

      <TweetComposer onSubmit={handleCreate} />

      {loading ? (
        <FeedSkeleton />
      ) : tweets.length === 0 ? (
        <div className="flex flex-col items-center text-center px-8 py-16 text-gray-500">
          <Sparkles className="mb-3 text-nextweet" size={32} />
          <p className="font-bold text-lg text-gray-900 mb-1">Welcome to Nextweet</p>
          <p className="text-sm">
            Your feed is empty. Follow people from the Explore tab to see their tweets here.
          </p>
        </div>
      ) : (
        tweets.map((t) => (
          <TweetCard key={t.id} tweet={t} onUpdate={handleUpdate} onDelete={handleDelete} />
        ))
      )}
    </div>
  );
}

function FeedSkeleton() {
  return (
    <div>
      {[...Array(4)].map((_, i) => (
        <div key={i} className="px-4 py-4 border-b border-gray-100 flex gap-3 animate-pulse">
          <div className="w-11 h-11 rounded-full bg-gray-200" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-1/3 bg-gray-200 rounded" />
            <div className="h-3 w-2/3 bg-gray-200 rounded" />
            <div className="h-3 w-1/2 bg-gray-200 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}
