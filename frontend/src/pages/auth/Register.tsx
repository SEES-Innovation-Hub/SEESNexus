import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import * as authApi from "../../api/auth";
import { errorMessage } from "../../api/client";
import Button from "../../components/Button";
import Card from "../../components/Card";
import TextField from "../../components/TextField";
import { useAuth } from "../../hooks/useAuth";
import { prefetchPages } from "../../routes/pageLoaders";
import { redirectPathForRole } from "../../utils/redirectPathForRole";
import { OtpVerification } from "./OtpVerification";

interface RegisterDetails {
  full_name: string;
  email: string;
  password: string;
  department: string;
  level: string;
}

const emptyDetails: RegisterDetails = {
  full_name: "",
  email: "",
  password: "",
  department: "",
  level: "",
};

export function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState<"details" | "otp">("details");
  const [details, setDetails] = useState<RegisterDetails>(emptyDetails);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField<K extends keyof RegisterDetails>(
    field: K,
    value: RegisterDetails[K],
  ) {
    setDetails((previous) => ({ ...previous, [field]: value }));
  }

  // Step 1: request an OTP for the entered email, then hand off to the OTP screen.
  async function handleDetailsSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await authApi.sendCode(details.email);
      setStep("otp");
    } catch {
      setError(
        "Could not send a verification code. Check the email and try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  // Step 2: the code is already verified by OtpVerification itself — this just
  // creates the account and logs the user straight in, so registration ends
  // on an authenticated session instead of a second login form. Verifying
  // uses the code up, so a failure here goes back to the details step (with
  // the backend's reason) where a fresh code will be requested.
  async function handleCodeVerified(code: string) {
    setError(null);
    setIsSubmitting(true);
    // Overlaps the home page's download with account creation and login.
    prefetchPages("projectsList");
    try {
      await authApi.register({ ...details, verification_code: code });
      const loggedInUser = await login(details.email, details.password);
      navigate(redirectPathForRole(loggedInUser.role));
    } catch (registerError) {
      setError(errorMessage(registerError, "Registration failed. Please try again."));
      setStep("details");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (step === "otp") {
    return (
      <OtpVerification
        email={details.email}
        isSubmitting={isSubmitting}
        onVerified={handleCodeVerified}
        onBack={() => setStep("details")}
      />
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4 sm:p-8">
      <Card padding="lg" className="w-full max-w-sm">
        <form onSubmit={handleDetailsSubmit} className="space-y-4">
          <h1 className="text-2xl font-semibold text-sees-mint">Create an account</h1>

          <TextField
            id="full_name"
            label="Full name"
            value={details.full_name}
            onChange={(v) => updateField("full_name", v)}
          />
          <TextField
            id="email"
            label="Email"
            type="email"
            value={details.email}
            onChange={(v) => updateField("email", v)}
          />
          <TextField
            id="password"
            label="Password"
            type="password"
            value={details.password}
            onChange={(v) => updateField("password", v)}
            minLength={8}
          />
          <TextField
            id="department"
            label="Department"
            value={details.department}
            onChange={(v) => updateField("department", v)}
          />
          <TextField
            id="level"
            label="Level"
            value={details.level}
            onChange={(v) => updateField("level", v)}
            required={false}
          />

          {error && <p className="text-sm text-red-400">{error}</p>}

          <Button type="submit" isLoading={isSubmitting} className="w-full">
            {isSubmitting ? "Sending code…" : "Continue"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
