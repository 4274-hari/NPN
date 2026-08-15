import { NavLink } from "react-router-dom";
import { Home, Search, Bell, Mail, User } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const ITEMS = [
  { to: "/home", icon: Home },
  { to: "/explore", icon: Search },
  { to: "/notifications", icon: Bell },
  { to: "/messages", icon: Mail },
];

export default function MobileNav() {
  const { user } = useAuth();
  return (
    <nav className="sm:hidden fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur border-t border-gray-100 flex items-center justify-around py-2 z-40">
      {ITEMS.map(({ to, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `p-2 rounded-full ${isActive ? "text-nextweet" : "text-gray-600"}`
          }
        >
          <Icon size={24} />
        </NavLink>
      ))}
      <NavLink
        to={`/profile/${user?.username}`}
        className={({ isActive }) => `p-2 rounded-full ${isActive ? "text-nextweet" : "text-gray-600"}`}
      >
        <User size={24} />
      </NavLink>
    </nav>
  );
}
