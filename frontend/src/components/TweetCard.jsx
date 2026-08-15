import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { formatDistanceToNowStrict } from "date-fns";
import { MessageCircle, Repeat2, Heart, Share, Trash2, Repeat } from "lucide-react";
import Avatar from "./Avatar";
import RichText from "./RichText";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

function timeAgo(iso) {
  try {
    return formatDistanceToNowStrict(new Date(iso), { addSuffix: false })
      .replace("seconds", "s")
      .replace("second", "s")
      .replace("minutes", "m")
      .replace("minute", "m")
      .replace("hours", "h")
      .replace("hour", "h")
      .replace("days", "d")
      .replace("day", "d")
      .replace(/ /g, "");
  } catch {
    return "";
  }
}

export default function TweetCard({ tweet, onDelete, onUpdate }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);

  if (!tweet || !tweet.author) return null;

  const isMine = tweet.author.id === user?.id;

  const goToTweet = () => navigate(`/tweet/${tweet.originalTweetId || tweet.id}`);
  const goToProfile = (e, username) => {
    e.stopPropagation();
    navigate(`/profile/${username}`);
  };

  const handleLike = async (e) => {
    e.stopPropagation();
    if (busy) return;
    setBusy(true);
    try {
      const targetId = tweet.originalTweetId || tweet.id;
      const res = tweet.isLiked
        ? await api.post(`/tweets/${targetId}/unlike`)
        : await api.post(`/tweets/${targetId}/like`);
      onUpdate?.(res.data);
    } finally {
      setBusy(false);
    }
  };

  const handleRetweet = async (e) => {
    e.stopPropagation();
    if (busy) return;
    setBusy(true);
    try {
      const targetId = tweet.originalTweetId || tweet.id;
      const res = tweet.isRetweeted
        ? await api.delete(`/tweets/${targetId}/retweet`)
        : await api.post(`/tweets/${targetId}/retweet`);
      onUpdate?.(res.data);
    } catch {
      // already retweeted race - ignore
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (!confirm("Delete this tweet?")) return;
    await api.delete(`/tweets/${tweet.id}`);
    onDelete?.(tweet.id);
  };

  const handleShare = (e) => {
    e.stopPropagation();
    const url = `${window.location.origin}/tweet/${tweet.originalTweetId || tweet.id}`;
    navigator.clipboard?.writeText(url);
  };

  return (
    <div
      onClick={goToTweet}
      className="px-4 py-3 border-b border-gray-100 hover:bg-gray-50/70 transition-colors cursor-pointer animate-fade-in"
    >
      {tweet.isRetweet && (
        <div className="flex items-center gap-2 text-gray-500 text-xs font-semibold mb-1 ml-7">
          <Repeat size={14} />
          <span>
            {tweet.retweetedBy?.id === user?.id ? "You" : tweet.retweetedBy?.displayName} reposted
          </span>
        </div>
      )}
      <div className="flex gap-3">
        <button onClick={(e) => goToProfile(e, tweet.author.username)}>
          <Avatar user={tweet.author} size={44} />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              onClick={(e) => goToProfile(e, tweet.author.username)}
              className="font-bold text-[15px] text-gray-900 hover:underline truncate"
            >
              {tweet.author.displayName}
            </button>
            <span className="text-gray-500 text-[15px] truncate">@{tweet.author.username}</span>
            <span className="text-gray-400 text-[15px]">·</span>
            <span className="text-gray-500 text-[15px]">{timeAgo(tweet.createdAt)}</span>
            {isMine && (
              <button
                onClick={handleDelete}
                className="ml-auto text-gray-400 hover:text-red-500 p-1.5 rounded-full hover:bg-red-50"
                title="Delete tweet"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>

          <div className="text-[15px] text-gray-900 mt-0.5 leading-normal">
            <RichText text={tweet.content} />
          </div>

          <div className="flex items-center justify-between mt-3 max-w-md text-gray-500">
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToTweet();
              }}
              className="flex items-center gap-1.5 group"
            >
              <span className="p-2 rounded-full group-hover:bg-nextweet/10 group-hover:text-nextweet transition-colors">
                <MessageCircle size={17} />
              </span>
              <span className="text-xs group-hover:text-nextweet">{tweet.repliesCount || ""}</span>
            </button>

            <button onClick={handleRetweet} className="flex items-center gap-1.5 group">
              <span
                className={`p-2 rounded-full group-hover:bg-green-50 group-hover:text-green-600 transition-colors ${
                  tweet.isRetweeted ? "text-green-600" : ""
                }`}
              >
                <Repeat2 size={18} />
              </span>
              <span className={`text-xs group-hover:text-green-600 ${tweet.isRetweeted ? "text-green-600" : ""}`}>
                {tweet.retweetsCount || ""}
              </span>
            </button>

            <button onClick={handleLike} className="flex items-center gap-1.5 group">
              <span
                className={`p-2 rounded-full group-hover:bg-pink-50 group-hover:text-pink-600 transition-colors ${
                  tweet.isLiked ? "text-pink-600 animate-like-pop" : ""
                }`}
              >
                <Heart size={17} fill={tweet.isLiked ? "currentColor" : "none"} />
              </span>
              <span className={`text-xs group-hover:text-pink-600 ${tweet.isLiked ? "text-pink-600" : ""}`}>
                {tweet.likesCount || ""}
              </span>
            </button>

            <button onClick={handleShare} className="flex items-center gap-1.5 group" title="Copy link">
              <span className="p-2 rounded-full group-hover:bg-nextweet/10 group-hover:text-nextweet transition-colors">
                <Share size={16} />
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
