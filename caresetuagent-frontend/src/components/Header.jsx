function Header() {
  return (
    <header className="bg-blue-600 text-white p-6 text-center shadow-lg">
      <h1 className="text-3xl font-bold">{import.meta.env.VITE_APP_NAME}</h1>
      <p className="text-blue-100 mt-2">
        Instant Voice Connection with AI Assistant
      </p>
    </header>
  );
}

export default Header;
