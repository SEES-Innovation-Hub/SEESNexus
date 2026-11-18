import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { errorMessage } from "../../api/client";
import Button from "../../components/Button";
import Card from "../../components/Card";
import PrefetchLink from "../../components/PrefetchLink";
import TextField from "../../components/TextField";
import { useAuth } from "../../hooks/useAuth";
import { prefetchPageForPath } from "../../routes/pageLoaders";
import { redirectPathForRole } from "../../utils/redirectPathForRole";
import { readReturnPath } from "../../utils/returnPath";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  // Set when a members-only page sent them here (ProtectedRoute).
  const returnPath = readReturnPath(useLocation().state);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    // Overlaps the next page's download with the login request instead of waiting for it.
    // Most people land on their Dashboard (admins on /admin, fetched on arrival).
    prefetchPageForPath(returnPath ?? "/dashboard");
    try {
      const loggedInUser = await login(email, password);
      navigate(returnPath ?? redirectPathForRole(loggedInUser.role), { replace: true });
    } catch (loginError) {
      setError(errorMessage(loginError, "Could not reach the server. Try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4 sm:p-8">
      <Card padding="lg" className="w-full max-w-sm">
        <form onSubmit={handleSubmit} className="space-y-4">
          <h1 className="text-2xl font-semibold text-sees-mint">Log in</h1>

          <TextField
            id="email"
            label="Email"
            type="email"
            value={email}
            onChange={setEmail}
          />
          <TextField
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
          />

          {error && <p className="text-sm text-red-400">{error}</p>}

          <Button type="submit" isLoading={isSubmitting} className="w-full">
            {isSubmitting ? "Logging in…" : "Log in"}
          </Button>

          <p className="text-sm text-white/60">
            No account?{" "}
            <PrefetchLink to="/register" className="-my-3 inline-block py-3 text-sees-mustard underline hover:text-sees-mint">
              Register
            </PrefetchLink>
          </p>
        </form>
      </Card>
    </div>
  );
}
