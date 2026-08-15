export default function PlaceholderPage({ title, description, icon: Icon }) {
  return (
    <div>
      <div className="sticky top-0 bg-white/90 backdrop-blur z-10 border-b border-gray-100 px-4 py-3">
        <h1 className="text-xl font-extrabold text-gray-900">{title}</h1>
      </div>
      <div className="flex flex-col items-center text-center px-8 py-20 text-gray-500">
        {Icon && <Icon className="mb-3 text-nextweet" size={32} />}
        <p className="font-bold text-lg text-gray-900 mb-1">{title}</p>
        <p className="text-sm max-w-xs">{description}</p>
      </div>
    </div>
  );
}
