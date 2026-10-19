
import { useEffect, useState } from "react";
import {
  confirmSignUp,
  getCurrentUser,
  signIn,
  signOut,
  signUp,
} from "aws-amplify/auth";
import App from "./App";

type Mode = "login" | "signup" | "confirm";

export default function AuthGate() {
  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmationCode, setConfirmationCode] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [checking, setChecking] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getCurrentUser()
      .then((user) => {
        setAuthenticated(true);
        if (user?.signInDetails?.loginId) {
          setUsername(user.signInDetails.loginId);
        } else if (user?.username) {
          setUsername(user.username);
        }
      })
      .catch(() => setAuthenticated(false))
      .finally(() => setChecking(false));
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setBusy(true);

    try {
      if (mode === "signup") {
        const result = await signUp({
          username: username.trim(),
          password,
          options: {
            userAttributes: {
              email: username.trim(),
            },
          },
        });

        if (result.nextStep.signUpStep === "CONFIRM_SIGN_UP") {
          setMode("confirm");
          setMessage("Check your email for the confirmation code.");
        } else {
          setMode("login");
          setMessage("Account created. Please sign in.");
        }
      } else if (mode === "confirm") {
        await confirmSignUp({
          username: username.trim(),
          confirmationCode: confirmationCode.trim(),
        });

        setMode("login");
        setPassword("");
        setConfirmationCode("");
        setMessage("Email confirmed. You can now sign in.");
      } else {
        const result = await signIn({
          username: username.trim(),
          password,
        });

        if (result.isSignedIn) {
          setAuthenticated(true);
        } else {
          setMessage(
            `Additional sign-in step required: ${result.nextStep.signInStep}. Check your Cognito sign-in settings.`
          );
        }
      }
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Authentication failed."
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleSignOut() {
    try {
      await signOut();
      setAuthenticated(false);
      setPassword("");
      setMessage("");
      setMode("login");
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Could not sign out."
      );
    }
  }

  if (checking) {
    return (
      <div className="min-h-screen bg-slate-950 text-white grid place-items-center">
        Checking your session...
      </div>
    );
  }

  if (authenticated) {
    return (
      <>
        <div className="flex items-center justify-end gap-3 bg-slate-900 px-5 py-3 text-sm text-white">
          <span>{username || "Signed in"}</span>
          <button
            onClick={handleSignOut}
            className="rounded-lg bg-rose-600 px-4 py-2 hover:bg-rose-500"
          >
            Sign out
          </button>
        </div>
        <App username={username} />
      </>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-5">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-5 rounded-2xl border border-slate-700 bg-slate-900 p-8 shadow-xl"
      >
        <div className="text-center">
          <h1 className="text-2xl font-bold text-emerald-400">
            Smart Finance Assistant
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            {mode === "login"
              ? "Sign in to access your dashboard"
              : mode === "signup"
                ? "Create your account"
                : "Verify your email"}
          </p>
        </div>

        {mode !== "confirm" && (
          <>
            <label className="block text-sm">
              Email
              <input
                type="email"
                required
                autoComplete="email"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 outline-none focus:border-emerald-500"
                placeholder="you@example.com"
              />
            </label>

            <label className="block text-sm">
              Password
              <input
                type="password"
                required
                minLength={8}
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 outline-none focus:border-emerald-500"
                placeholder="Enter your password"
              />
            </label>
          </>
        )}

        {mode === "confirm" && (
          <label className="block text-sm">
            Email confirmation code
            <input
              required
              value={confirmationCode}
              onChange={(event) => setConfirmationCode(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 outline-none focus:border-emerald-500"
              placeholder="Enter the code from your email"
            />
          </label>
        )}

        {message && (
          <p role="status" className="break-words text-sm text-amber-300">
            {message}
          </p>
        )}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-emerald-500 p-3 font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy
            ? "Please wait..."
            : mode === "login"
              ? "Sign in"
              : mode === "signup"
                ? "Create account"
                : "Confirm email"}
        </button>

        {mode !== "confirm" && (
          <p className="text-center text-sm text-slate-400">
            {mode === "login" ? "New here?" : "Already have an account?"}{" "}
            <button
              type="button"
              className="text-emerald-400 hover:underline"
              onClick={() => {
                setMode(mode === "login" ? "signup" : "login");
                setMessage("");
              }}
            >
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </p>
        )}

        {mode === "confirm" && (
          <button
            type="button"
            className="w-full text-sm text-emerald-400 hover:underline"
            onClick={() => {
              setMode("login");
              setMessage("");
            }}
          >
            Back to sign in
          </button>
        )}
      </form>
    </main>
  );
}
