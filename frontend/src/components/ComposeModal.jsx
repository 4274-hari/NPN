import { X } from "lucide-react";
import TweetComposer from "./TweetComposer";

export default function ComposeModal({ open, onClose, onSubmit }) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 bg-black/40 z-50 flex items-start justify-center pt-10 sm:pt-20 px-2 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl w-full max-w-xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-3 py-2">
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100">
            <X size={20} />
          </button>
        </div>
        <TweetComposer
          autoFocus
          buttonLabel="Tweet"
          onSubmit={async (content) => {
            await onSubmit(content);
            onClose();
          }}
        />
      </div>
    </div>
  );
}
