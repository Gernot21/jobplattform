import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Briefcase, UserCircle2 } from "lucide-react";
import { toast } from "sonner";

export default function Onboarding() {
  const navigate = useNavigate();
  const { hydrate, user } = useAuth();
  const { t } = useI18n();
  const [busy, setBusy] = useState(null);

  // If user already has a role, send them home
  if (user && user.role) {
    navigate(`/${user.role}`, { replace: true });
  }

  const choose = async (role) => {
    setBusy(role);
    try {
      const { data } = await api.post("/auth/onboarding", { role });
      localStorage.setItem("token", data.token);
      await hydrate();
      toast.success("Willkommen!");
      navigate(`/${role}`, { replace: true });
    } catch (e) {
      toast.error(e.response?.data?.detail || "Fehler");
      setBusy(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6" data-testid="onboarding-page">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-10">
          <h1 className="font-display text-4xl font-bold text-slate-900">Willkommen bei Teilzeit.Jobs</h1>
          <p className="text-slate-500 mt-3 text-lg">Sag uns kurz, wer du bist – das bestimmt deine persönliche Ansicht.</p>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          {[
            { id: "employee", label: t("employee"), desc: "Ich suche eine Teilzeitstelle 20–80%.", Icon: UserCircle2 },
            { id: "employer", label: t("employer"), desc: "Ich biete eine Teilzeitstelle für mein Unternehmen an.", Icon: Briefcase },
          ].map(({ id, label, desc, Icon }) => (
            <Card key={id} className="card-hover cursor-pointer" data-testid={`onboarding-${id}`} onClick={() => !busy && choose(id)}>
              <CardContent className="p-8 flex flex-col items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 flex items-center justify-center">
                  <Icon className="w-6 h-6 text-emerald-600" />
                </div>
                <h2 className="font-display text-2xl font-bold text-slate-900">{label}</h2>
                <p className="text-slate-600">{desc}</p>
                <Button
                  className="mt-2 bg-slate-900 hover:bg-slate-800 text-white"
                  disabled={busy === id}
                  onClick={(e) => { e.stopPropagation(); choose(id); }}
                  data-testid={`onboarding-select-${id}`}
                >
                  {busy === id ? "..." : "Auswählen"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
