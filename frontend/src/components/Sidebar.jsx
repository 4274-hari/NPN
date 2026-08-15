import { NavLink, useNavigate } from "react-router-dom";
import {
  Home,
  Search,
  Bell,
  Mail,
  Bookmark,
  ListChecks,
  User,
  MoreHorizontal,
  Feather,
  LogOut,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import Avatar from "./Avatar";
import { useState } from "react";

const NAV_ITEMS = [
  { to: "/home", label: "Home", icon: Home },
  { to: "/explore", label: "Explore", icon: Search },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/messages", label: "Messages", icon: Mail },
  { to: "/bookmarks", label: "Bookmarks", icon: Bookmark },
  { to: "/lists", label: "Lists", icon: ListChecks },
];

export default function Sidebar({ onCompose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <aside className="hidden sm:flex flex-col justify-between h-screen sticky top-0 py-2 px-2 lg:px-4 w-[70px] lg:w-[260px] flex-shrink-0 border-r border-gray-100">
      <div>
        <div className="flex items-center gap-2 px-2 lg:px-3 py-3 mb-1">
          <div className="w-9 h-9 rounded-full bg-nextweet flex items-center justify-center text-white font-extrabold text-lg">
            N
          </div>
          <span className="hidden lg:inline text-xl font-extrabold text-gray-900">Nextweet</span>
        </div>

        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-4 px-3 py-3 rounded-full transition-colors text-[17px] ${
                  isActive
                    ? "font-bold text-nextweet bg-nextweet/10"
                    : "text-gray-800 hover:bg-gray-100"
                }`
              }
            >
              <Icon size={24} strokeWidth={2.2} />
              <span className="hidden lg:inline">{label}</span>
            </NavLink>
          ))}
          <NavLink
            to={`/profile/${user?.username}`}
            className={({ isActive }) =>
              `flex items-center gap-4 px-3 py-3 rounded-full transition-colors text-[17px] ${
                isActive ? "font-bold text-nextweet bg-nextweet/10" : "text-gray-800 hover:bg-gray-100"
              }`
            }
          >
            <User size={24} strokeWidth={2.2} />
            <span className="hidden lg:inline">Profile</span>
          </NavLink>
          <button
            className="flex items-center gap-4 px-3 py-3 rounded-full transition-colors text-[17px] text-gray-800 hover:bg-gray-100 text-left"
            onClick={() => setMenuOpen((v) => !v)}
          >
            <MoreHorizontal size={24} strokeWidth={2.2} />
            <span className="hidden lg:inline">More</span>
          </button>
          {menuOpen && (
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="flex items-center gap-4 px-3 py-3 ml-2 rounded-full text-[15px] text-red-600 hover:bg-red-50"
            >
              <LogOut size={20} />
              <span className="hidden lg:inline">Log out</span>
            </button>
          )}
        </nav>

        <button
          onClick={onCompose}
          className="mt-4 w-full lg:w-[90%] bg-nextweet hover:bg-nextweet-dark text-white font-bold rounded-full py-3 transition-colors flex items-center justify-center gap-2 shadow-sm"
        >
          <Feather size={20} className="lg:hidden" />
          <span className="hidden lg:inline">Tweet</span>
        </button>
      </div>

      {user && (
        <button
          onClick={() => navigate(`/profile/${user.username}`)}
          className="flex items-center gap-3 px-2 py-3 rounded-full hover:bg-gray-100 mb-2"
        >
          <Avatar user={user} size={40} />
          <div className="hidden lg:block text-left min-w-0">
            <p className="font-bold text-sm truncate">{user.displayName}</p>
            <p className="text-gray-500 text-sm truncate">@{user.username}</p>
          </div>
        </button>
      )}
    </aside>
  );
}
