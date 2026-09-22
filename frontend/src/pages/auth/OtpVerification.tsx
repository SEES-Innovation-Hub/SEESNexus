import { useState, type FormEvent } from "react";
import * as authApi from "../../api/auth";
import { errorMessage } from "../../api/client";
import TextField from "../../components/TextField";

interface OtpVerificationProps {
  email: string;
  isSubmitting: boolean;
  onVerified: (code: string) => void;
  onBack: () => void;
}

export function OtpVerification({
  email,
  isSubmitting,
  onVerified,
  onBack,
}: OtpVerificationProps) {
  const [code, setCode] = useState("");
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setVerifyError(null);
    setIsVerifying(true);
    try {
      await authApi.verifyCode(email, code);
      onVerified(code);
    } catch (error) {
      setVerifyError(errorMessage(error, "Could not verify the code. Try again."));
    } finally {
      setIsVerifying(false);
    }
  }

  const isBusy = isVerifying || isSubmitting;

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-2xl border border-sees-teal/40 bg-gradient-card p-8 shadow-sees-card"
      >
        <h1 className="text-2xl font-semibold text-sees-mint">Verify your email</h1>
        <p className="text-sm wrap-anywhere text-white/60">We sent a code to {email}.</p>

        <TextField
          id="otp"
          label="Verification code"
          value={code}
          onChange={setCode}
        />

        {verifyError && <p className="text-sm text-red-400">{verifyError}</p>}

        <button
          type="submit"
          disabled={isBusy}
          className="w-full rounded bg-sees-mint py-2.5 font-medium text-sees-forest transition-shadow hover:shadow-sees-glow disabled:opacity-50"
        >
          {isVerifying
            ? "Verifying…"
            : isSubmitting
              ? "Creating account…"
              : "Verify"}
        </button>

        <button
          type="button"
          onClick={onBack}
          className="w-full py-3 text-sm text-sees-mustard underline hover:text-sees-mint"
        >
          Back
        </button>
      </form>
    </div>
  );
}
