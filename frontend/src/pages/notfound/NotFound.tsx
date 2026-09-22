import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-2xl font-semibold text-sees-mint">Page not found</h1>
      <p className="text-sm text-white/60">
        This page doesn't exist, or hasn't been built yet.
      </p>
      <Link to="/" className="text-sm text-sees-mustard underline hover:text-sees-mint">
        Back to home
      </Link>
    </div>
  );
}
