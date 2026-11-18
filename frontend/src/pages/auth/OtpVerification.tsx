import { useState, type FormEvent } from "react";
import * as authApi from "../../api/auth";
import { errorMessage } from "../../api/client";
import Button from "../../components/Button";
import Card from "../../components/Card";
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
    <main className="flex min-h-screen items-center justify-center p-4 sm:p-8">
      <Card padding="lg" className="w-full max-w-sm">
        <form onSubmit={handleSubmit} className="space-y-4">
          <h1 className="text-2xl font-semibold text-sees-mint">Verify your email</h1>
          <p className="text-sm wrap-anywhere text-white/60">We sent a code to {email}.</p>

          <TextField
            id="otp"
            label="Verification code"
            value={code}
            onChange={setCode}
          />

          {verifyError && <p className="text-sm text-red-400">{verifyError}</p>}

          <Button type="submit" isLoading={isBusy} className="w-full">
            {isVerifying
              ? "Verifying…"
              : isSubmitting
                ? "Creating account…"
                : "Verify"}
          </Button>

          <Button variant="secondary" onClick={onBack} className="w-full">
            Back
          </Button>
        </form>
      </Card>
    </main>
  );
}
