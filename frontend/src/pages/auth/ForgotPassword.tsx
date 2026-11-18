import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import * as authApi from "../../api/auth";
import { errorMessage } from "../../api/client";
import Button from "../../components/Button";
import { textLinkClassName } from "../../components/Button/textLinkClassName";
import Card from "../../components/Card";
import PrefetchLink from "../../components/PrefetchLink";
import TextField from "../../components/TextField";

const MIN_PASSWORD = 8;

// Two steps on one page: the email, then the emailed code and a new password.
// The first step answers the same whether or not the address has an account,
// so this page never reveals who is registered.
export function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState<"email" | "reset">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function requestCode(event?: FormEvent) {
    event?.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await authApi.forgotPassword(email.trim());
      setStep("reset");
    } catch (requestError) {
      setError(errorMessage(requestError, "Couldn't send the code. Try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleReset(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (password.length < MIN_PASSWORD) {
      setError(`Use at least ${MIN_PASSWORD} characters.`);
      return;
    }
    if (password !== confirm) {
      setError("The two passwords don't match.");
      return;
    }
    setIsSubmitting(true);
    try {
      await authApi.resetPassword(email.trim(), code.trim(), password);
      navigate("/login", {
        replace: true,
        state: { notice: "Password changed. Log in with your new password." },
      });
    } catch (resetError) {
      setError(errorMessage(resetError, "Couldn't change the password. Try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4 sm:p-8">
      <Card padding="lg" className="w-full max-w-sm">
        {step === "email" ? (
          <form onSubmit={requestCode} className="space-y-4">
            <h1 className="text-2xl font-semibold text-sees-mint">Reset your password</h1>
            <p className="text-sm text-white/60">Enter your account's email and we'll send you a code.</p>
            <TextField id="email" label="Email" type="email" value={email} onChange={setEmail} />
            {error && (
              <p role="alert" className="text-sm text-red-400">
                {error}
              </p>
            )}
            <Button type="submit" isLoading={isSubmitting} className="w-full">
              Send code
            </Button>
            <p className="text-sm text-white/60">
              Remembered it?{" "}
              <PrefetchLink to="/login" className={`-my-3 inline-block py-3 ${textLinkClassName}`}>
                Log in
              </PrefetchLink>
            </p>
          </form>
        ) : (
          <form onSubmit={handleReset} className="space-y-4">
            <h1 className="text-2xl font-semibold text-sees-mint">Choose a new password</h1>
            <p className="text-sm wrap-anywhere text-white/60">
              If {email.trim()} has an account, a code is on its way. It expires in 10 minutes.
            </p>
            <TextField
              id="reset-code"
              label="Code from the email"
              value={code}
              onChange={setCode}
              autoComplete="one-time-code"
              maxLength={10}
            />
            <TextField
              id="new-password"
              label="New password"
              type="password"
              value={password}
              onChange={setPassword}
              autoComplete="new-password"
              minLength={MIN_PASSWORD}
              hint={`At least ${MIN_PASSWORD} characters. You'll be signed out everywhere else.`}
            />
            <TextField
              id="confirm-password"
              label="New password again"
              type="password"
              value={confirm}
              onChange={setConfirm}
              autoComplete="new-password"
            />
            {error && (
              <p role="alert" className="text-sm text-red-400">
                {error}
              </p>
            )}
            <Button type="submit" isLoading={isSubmitting} className="w-full">
              Change password
            </Button>
            <div className="flex flex-wrap justify-between gap-2 text-sm">
              <button
                type="button"
                onClick={() => void requestCode()}
                disabled={isSubmitting}
                className={`-my-3 py-3 ${textLinkClassName} disabled:opacity-50`}
              >
                Send a new code
              </button>
              <button
                type="button"
                onClick={() => {
                  setStep("email");
                  setError(null);
                }}
                className="-my-3 py-3 text-white/60 underline hover:text-white"
              >
                Use a different email
              </button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
