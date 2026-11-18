import { Link } from "react-router-dom";
import { buttonClassName } from "../../components/Button/buttonClassName";

export function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-2xl font-semibold text-sees-mint">Page not found</h1>
      <p className="text-sm text-white/60">
        This page doesn't exist. Check the link, or go back home.
      </p>
      <Link to="/" className={buttonClassName("secondary")}>
        Back to home
      </Link>
    </main>
  );
}
