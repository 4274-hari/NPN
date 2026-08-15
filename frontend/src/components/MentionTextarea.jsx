import { useState, useRef, useEffect, useCallback } from "react";
import api from "../api/client";
import Avatar from "./Avatar";

/**
 * A textarea that shows an @mention autocomplete dropdown as the user types.
 * - Typing "@n" fetches and shows matching users (username or display name).
 * - ArrowUp / ArrowDown move the highlighted suggestion, Enter/Tab selects it,
 *   Escape closes the dropdown.
 * - Clicking a suggestion inserts "@username " at the mention's position.
 * - Clicking outside or clearing the match closes the dropdown.
 */
export default function MentionTextarea({
  value,
  onChange,
  placeholder = "What's happening?",
  rows = 3,
  autoFocus = false,
  className = "",
  onSubmitShortcut,
}) {
  const textareaRef = useRef(null);
  const wrapperRef = useRef(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [mentionRange, setMentionRange] = useState(null); // {start, end}
  const debounceRef = useRef(null);

  // find "@query" fragment ending at the cursor
  const findMentionAtCursor = useCallback((text, cursorPos) => {
    const upToCursor = text.slice(0, cursorPos);
    const match = upToCursor.match(/(^|\s)@(\w*)$/);
    if (!match) return null;
    const query = match[2];
    const start = upToCursor.length - query.length - 1; // position of '@'
    return { start, end: cursorPos, query };
  }, []);

  const fetchSuggestions = useCallback((query) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await api.get("/users/mention-suggest", { params: { q: query } });
        setSuggestions(res.data);
        setShowDropdown(res.data.length > 0);
        setActiveIndex(0);
      } catch {
        setSuggestions([]);
        setShowDropdown(false);
      }
    }, 120);
  }, []);

  const handleChange = (e) => {
    const text = e.target.value;
    onChange(text);
    const cursorPos = e.target.selectionStart;
    const mention = findMentionAtCursor(text, cursorPos);
    if (mention) {
      setMentionRange(mention);
      fetchSuggestions(mention.query);
    } else {
      setShowDropdown(false);
      setMentionRange(null);
    }
  };

  const insertMention = (user) => {
    if (!mentionRange) return;
    const before = value.slice(0, mentionRange.start);
    const after = value.slice(mentionRange.end);
    const newValue = `${before}@${user.username} ${after}`;
    onChange(newValue);
    setShowDropdown(false);
    setMentionRange(null);

    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      const cursor = before.length + user.username.length + 2;
      el.focus();
      el.setSelectionRange(cursor, cursor);
    });
  };

  const handleKeyDown = (e) => {
    if (showDropdown && suggestions.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((i) => (i + 1) % suggestions.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((i) => (i - 1 + suggestions.length) % suggestions.length);
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        insertMention(suggestions[activeIndex]);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setShowDropdown(false);
        return;
      }
    }
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && onSubmitShortcut) {
      onSubmitShortcut();
    }
  };

  // close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={wrapperRef}>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={rows}
        autoFocus={autoFocus}
        className={`w-full resize-none border-none outline-none text-[15px] sm:text-[17px] placeholder-gray-400 bg-transparent ${className}`}
      />

      {showDropdown && suggestions.length > 0 && (
        <div className="absolute z-30 left-0 top-full mt-1 w-72 max-w-[90vw] bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden animate-fade-in">
          {suggestions.map((s, idx) => (
            <button
              key={s.id}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                insertMention(s);
              }}
              onMouseEnter={() => setActiveIndex(idx)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                idx === activeIndex ? "bg-nextweet/10" : "hover:bg-gray-50"
              }`}
            >
              <Avatar user={s} size={36} />
              <div className="min-w-0">
                <p className="font-semibold text-sm text-gray-900 truncate">{s.displayName}</p>
                <p className="text-sm text-gray-500 truncate">@{s.username}</p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
