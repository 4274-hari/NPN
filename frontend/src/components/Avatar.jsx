export default function Avatar({ user, size = 40, className = "" }) {
  const src =
    user?.avatarUrl ||
    `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.username || "guest"}`;
  return (
    <img
      src={src}
      alt={user?.displayName || user?.username || "user"}
      style={{ width: size, height: size }}
      className={`rounded-full object-cover bg-gray-100 flex-shrink-0 ${className}`}
    />
  );
}
