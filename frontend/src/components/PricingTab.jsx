import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, Sparkles, Crown, Zap, Building2 } from "lucide-react";
import { toast } from "sonner";

const TIER_META = {
  tier_1: { icon: Sparkles, color: "slate", testid: "tier-1" },
  tier_2: { icon: Zap, color: "emerald", testid: "tier-2" },
  tier_3: { icon: Crown, color: "blue", testid: "tier-3" },
  tier_4: { icon: Building2, color: "amber", testid: "tier-4" },
};

export default function PricingTab({ subscription, onChange }) {
  const { t } = useI18n();
  const [tiers, setTiers] = useState([]);
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    api.get("/tiers").then(({ data }) => setTiers(data));
  }, []);

  const upgrade = async (tier_id) => {
    setBusy(tier_id);
    try {
      const { data } = await api.post("/employer/checkout", {
        tier_id,
        origin_url: window.location.origin,
      });
      window.location.href = data.url;
    } catch (e) {
      toast.error(e.response?.data?.detail || "Upgrade fehlgeschlagen");
      setBusy(null);
    }
  };

  const currentTier = subscription?.tier?.id;

  return (
    <div className="space-y-6" data-testid="pricing-tab">
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="font-display text-xl font-semibold text-slate-900">Preisstruktur</h3>
        <p className="text-sm text-slate-500 mt-1">
          Arbeitnehmer:innen sind immer kostenlos. Wähle dein Abo als Arbeitgeber.
        </p>
      </div>

      <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-5">
        {tiers.map((tier) => {
          const meta = TIER_META[tier.id] || TIER_META.tier_1;
          const Icon = meta.icon;
          const isCurrent = currentTier === tier.id;
          const colorMap = {
            slate: "border-slate-200",
            emerald: "border-emerald-200",
            blue: "border-blue-200",
            amber: "border-amber-200",
          };
          return (
            <Card
              key={tier.id}
              className={`relative ${colorMap[meta.color]} ${isCurrent ? "ring-2 ring-emerald-500" : ""}`}
              data-testid={`pricing-card-${tier.id}`}
            >
              {isCurrent && (
                <div className="absolute -top-2.5 left-1/2 -translate-x-1/2">
                  <Badge className="bg-emerald-600 text-white border-0">Aktuelles Abo</Badge>
                </div>
              )}
              <CardContent className="p-6">
                <div className={`w-10 h-10 rounded-lg bg-${meta.color}-50 flex items-center justify-center mb-4`}>
                  <Icon className={`w-5 h-5 text-${meta.color}-600`} />
                </div>
                <h3 className="font-display text-xl font-bold text-slate-900">{tier.name}</h3>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="font-display text-3xl font-bold text-slate-900">
                    {tier.price === 0 ? "0" : tier.price}
                  </span>
                  <span className="text-sm text-slate-500">CHF / {tier.interval === "year" ? "Jahr" : "Monat"}</span>
                </div>
                <div className="mt-2 text-sm font-medium text-emerald-700">
                  {tier.max_postings === -1
                    ? "Unbegrenzte Inserate"
                    : `${tier.max_postings} Inserate / ${tier.period === "year" ? "Jahr" : "Monat"}`}
                </div>
                <ul className="mt-5 space-y-2 text-sm text-slate-700">
                  {tier.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Check className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-6">
                  {tier.id === "tier_1" ? (
                    <Button variant="outline" className="w-full" disabled data-testid={`select-${tier.id}`}>
                      {isCurrent ? "Aktiv" : "Standard"}
                    </Button>
                  ) : isCurrent ? (
                    <Button variant="outline" className="w-full" disabled data-testid={`select-${tier.id}`}>
                      Aktiv
                    </Button>
                  ) : (
                    <Button
                      onClick={() => upgrade(tier.id)}
                      disabled={busy === tier.id}
                      className={meta.color === "amber"
                        ? "w-full bg-amber-600 hover:bg-amber-700 text-white"
                        : "w-full bg-emerald-600 hover:bg-emerald-700 text-white"}
                      data-testid={`upgrade-${tier.id}`}
                    >
                      {busy === tier.id ? "Weiterleitung…" : `Upgrade auf ${tier.name}`}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <p className="text-xs text-slate-500">
        Zahlung sicher abgewickelt über Stripe. Kontingent wird am 1. jedes Monats (bzw. Jahres bei Starter) zurückgesetzt.
      </p>
    </div>
  );
}
