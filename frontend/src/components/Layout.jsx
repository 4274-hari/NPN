import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import RightSidebar from "./RightSidebar";
import MobileNav from "./MobileNav";
import ComposeModal from "./ComposeModal";
import api from "../api/client";

export default function Layout() {
  const [composeOpen, setComposeOpen] = useState(false);

  const handleCompose = async (content) => {
    await api.post("/tweets", { content });
    window.location.reload();
  };

  return (
    <div className="max-w-[1300px] mx-auto flex">
      <Sidebar onCompose={() => setComposeOpen(true)} />
      <main className="flex-1 min-w-0 border-r border-gray-100 max-w-[600px] pb-16 sm:pb-0">
        <Outlet />
      </main>
      <RightSidebar />
      <MobileNav />
      <ComposeModal open={composeOpen} onClose={() => setComposeOpen(false)} onSubmit={handleCompose} />
    </div>
  );
}
