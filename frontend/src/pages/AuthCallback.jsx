import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

/**
 * Handles redirect from Emergent Google Auth.
 * URL fragment: #session_id=XXX
 *
 * REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
 */
export default function AuthCallback() {
  const navigate = useNavigate();
  const { hydrate, setTwoFactor } = useAuth();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const hash = window.location.hash || "";
    const m = hash.match(/session_id=([^&]+)/);
    const session_id = m ? decodeURIComponent(m[1]) : null;
    if (!session_id) {
      navigate("/");
      return;
    }

    (async () => {
      try {
        const { data } = await api.post("/auth/google/exchange", { session_id });
        // Clean URL hash
        window.history.replaceState(null, "", "/");

        if (data.requires_2fa) {
          setTwoFactor(data.challenge_token);
          navigate("/");
          return;
        }
        localStorage.setItem("token", data.token);
        await hydrate();
        if (data.user && (!data.user.role || data.user.needs_onboarding)) {
          navigate("/onboarding", { replace: true });
        } else {
          navigate(`/${data.user.role}`, { replace: true });
        }
      } catch (e) {
        toast.error(e.response?.data?.detail || "Login fehlgeschlagen");
        navigate("/");
      }
    })();
    // eslint-disable-next-line
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-slate-500" data-testid="auth-callback">
      <Loader2 className="w-7 h-7 animate-spin mb-3 text-emerald-600" />
      Anmeldung wird abgeschlossen…
    </div>
  );
}
