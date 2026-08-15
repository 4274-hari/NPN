import { Link } from "react-router-dom";

const TOKEN_RE = /(@\w+|#\w+)/g;

export default function RichText({ text }) {
  const parts = (text || "").split(TOKEN_RE);
  return (
    <span className="whitespace-pre-wrap break-words">
      {parts.map((part, i) => {
        if (part.startsWith("@")) {
          return (
            <Link
              key={i}
              to={`/profile/${part.slice(1)}`}
              onClick={(e) => e.stopPropagation()}
              className="text-nextweet hover:underline font-medium"
            >
              {part}
            </Link>
          );
        }
        if (part.startsWith("#")) {
          return (
            <Link
              key={i}
              to={`/explore?q=${encodeURIComponent(part)}`}
              onClick={(e) => e.stopPropagation()}
              className="text-nextweet hover:underline font-medium"
            >
              {part}
            </Link>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}
