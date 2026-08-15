import { useState } from "react";
import { Image, Smile, MapPin, Calendar } from "lucide-react";
import Avatar from "./Avatar";
import MentionTextarea from "./MentionTextarea";
import { useAuth } from "../context/AuthContext";

const MAX_LEN = 500;

export default function TweetComposer({
  onSubmit,
  placeholder = "What's happening?",
  buttonLabel = "Tweet",
  autoFocus = false,
  compact = false,
}) {
  const { user } = useAuth();
  const [content, setContent] = useState("");
  const [posting, setPosting] = useState(false);

  const remaining = MAX_LEN - content.length;
  const canPost = content.trim().length > 0 && remaining >= 0 && !posting;

  const handleSubmit = async () => {
    if (!canPost) return;
    setPosting(true);
    try {
      await onSubmit(content.trim());
      setContent("");
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className={`flex gap-3 ${compact ? "py-3" : "p-4"} border-b border-gray-100`}>
      <Avatar user={user} size={44} />
      <div className="flex-1 min-w-0">
        <MentionTextarea
          value={content}
          onChange={setContent}
          placeholder={placeholder}
          rows={compact ? 2 : 3}
          autoFocus={autoFocus}
          className="min-h-[48px]"
          onSubmitShortcut={handleSubmit}
        />
        <div className="flex items-center justify-between mt-2 pt-3 border-t border-gray-50">
          <div className="flex items-center gap-1 text-nextweet">
            <button className="p-2 rounded-full hover:bg-nextweet/10" title="Media (demo)">
              <Image size={19} />
            </button>
            <button className="p-2 rounded-full hover:bg-nextweet/10" title="Emoji (demo)">
              <Smile size={19} />
            </button>
            <button className="p-2 rounded-full hover:bg-nextweet/10" title="Location (demo)">
              <MapPin size={19} />
            </button>
            <button className="p-2 rounded-full hover:bg-nextweet/10" title="Schedule (demo)">
              <Calendar size={19} />
            </button>
          </div>
          <div className="flex items-center gap-3">
            {content.length > 0 && (
              <span
                className={`text-xs font-medium ${
                  remaining < 0 ? "text-red-500" : remaining < 30 ? "text-amber-500" : "text-gray-400"
                }`}
              >
                {remaining}
              </span>
            )}
            <button
              onClick={handleSubmit}
              disabled={!canPost}
              className="bg-nextweet hover:bg-nextweet-dark disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-full px-5 py-2 text-sm transition-colors"
            >
              {posting ? "Posting…" : buttonLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
