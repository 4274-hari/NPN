import { Routes, Route, Navigate } from "react-router-dom";
import { Mail, Bookmark, ListChecks } from "lucide-react";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import Explore from "./pages/Explore";
import Notifications from "./pages/Notifications";
import Profile from "./pages/Profile";
import FollowList from "./pages/FollowList";
import TweetDetail from "./pages/TweetDetail";
import PlaceholderPage from "./pages/PlaceholderPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/home" element={<Home />} />
          <Route path="/explore" element={<Explore />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/tweet/:id" element={<TweetDetail />} />
          <Route path="/profile/:username" element={<Profile />} />
          <Route path="/profile/:username/followers" element={<FollowList mode="followers" />} />
          <Route path="/profile/:username/following" element={<FollowList mode="following" />} />
          <Route
            path="/messages"
            element={
              <PlaceholderPage
                title="Messages"
                description="Direct messages are coming soon to Nextweet."
                icon={Mail}
              />
            }
          />
          <Route
            path="/bookmarks"
            element={
              <PlaceholderPage
                title="Bookmarks"
                description="Save tweets for later — coming soon."
                icon={Bookmark}
              />
            }
          />
          <Route
            path="/lists"
            element={
              <PlaceholderPage
                title="Lists"
                description="Create curated lists of accounts — coming soon."
                icon={ListChecks}
              />
            }
          />
        </Route>

        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </AuthProvider>
  );
}
