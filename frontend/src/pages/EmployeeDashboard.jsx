import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { useI18n } from "@/lib/i18n";
import { api } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Loader2, MapPin, Sparkles, CheckCircle2 } from "lucide-react";

function ScoreRing({ score }) {
  const color = score >= 80 ? "#10b981" : score >= 60 ? "#0ea5e9" : score >= 40 ? "#f59e0b" : "#94a3b8";
  return (
    <div
      className="relative w-16 h-16 rounded-full flex items-center justify-center"
      style={{ background: `conic-gradient(${color} ${score}%, #e2e8f0 0)` }}
      data-testid="match-score-ring"
    >
      <div className="absolute inset-1.5 rounded-full bg-white flex flex-col items-center justify-center">
        <span className="font-display font-bold text-lg leading-none" style={{ color }}>{score}</span>
        <span className="text-[9px] text-slate-500 uppercase">match</span>
      </div>
    </div>
  );
}

export default function EmployeeDashboard() {
  const { t } = useI18n();
  const [tab, setTab] = useState("profile");
  const [profile, setProfile] = useState({
    first_name: "",
    last_name: "",
    core_skills: "",
    key_experiences: "",
    looking_for: "",
    desired_percentage_min: 20,
    desired_percentage_max: 80,
  });
  const [hasProfile, setHasProfile] = useState(false);
  const [suggested, setSuggested] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(false);

  useEffect(() => {
    loadProfile();
    loadApplications();
  }, []);

  const loadProfile = async () => {
    const { data } = await api.get("/employee/profile");
    if (data && data.first_name) {
      setProfile({ ...profile, ...data });
      setHasProfile(true);
    }
  };

  const loadApplications = async () => {
    const { data } = await api.get("/employee/applications");
    setApplications(data);
  };

  const loadSuggested = async () => {
    setLoadingMatches(true);
    try {
      const { data } = await api.get("/employee/jobs/suggested");
      setSuggested(data);
    } finally {
      setLoadingMatches(false);
    }
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    try {
      await api.put("/employee/profile", profile);
      setHasProfile(true);
      toast.success("Profil gespeichert");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Fehler");
    }
  };

  const apply = async (jobId, coverLetter = "") => {
    try {
      await api.post("/employee/applications", { job_id: jobId, cover_letter: coverLetter });
      toast.success("Bewerbung gesendet");
      loadSuggested();
      loadApplications();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Fehler");
    }
  };

  return (
    <div className="min-h-screen">
      <Header title={t("employee")} />
      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8" data-testid="employee-dashboard">
        <h1 className="font-display text-3xl font-bold text-slate-900 mb-1">{t("welcome")}</h1>
        <p className="text-slate-500 mb-8">{t("subtagline")}</p>

        <Tabs value={tab} onValueChange={(v) => { setTab(v); if (v === "suggested") loadSuggested(); }}>
          <TabsList className="bg-white border border-slate-200 p-1">
            <TabsTrigger value="profile" data-testid="emp-tab-profile">{t("profile")}</TabsTrigger>
            <TabsTrigger value="suggested" data-testid="emp-tab-suggested">{t("suggested")}</TabsTrigger>
            <TabsTrigger value="applied" data-testid="emp-tab-applied">{t("applied")}</TabsTrigger>
          </TabsList>

          {/* Profile */}
          <TabsContent value="profile" className="mt-6">
            <Card>
              <CardHeader><CardTitle className="font-display">{t("profile")}</CardTitle></CardHeader>
              <CardContent>
                <form onSubmit={saveProfile} className="grid sm:grid-cols-2 gap-5">
                  <div>
                    <Label>{t("firstName")}</Label>
                    <Input value={profile.first_name} onChange={(e) => setProfile({ ...profile, first_name: e.target.value })} required data-testid="emp-first-name" className="mt-1.5" />
                  </div>
                  <div>
                    <Label>{t("lastName")}</Label>
                    <Input value={profile.last_name} onChange={(e) => setProfile({ ...profile, last_name: e.target.value })} required data-testid="emp-last-name" className="mt-1.5" />
                  </div>
                  <div className="sm:col-span-2">
                    <Label>{t("coreSkills")}</Label>
                    <Textarea value={profile.core_skills} onChange={(e) => setProfile({ ...profile, core_skills: e.target.value })} rows={3} required data-testid="emp-core-skills" className="mt-1.5" />
                  </div>
                  <div className="sm:col-span-2">
                    <Label>{t("keyExperiences")}</Label>
                    <Textarea value={profile.key_experiences} onChange={(e) => setProfile({ ...profile, key_experiences: e.target.value })} rows={3} required data-testid="emp-key-experiences" className="mt-1.5" />
                  </div>
                  <div className="sm:col-span-2">
                    <Label>{t("lookingFor")}</Label>
                    <Textarea value={profile.looking_for} onChange={(e) => setProfile({ ...profile, looking_for: e.target.value })} rows={3} required data-testid="emp-looking-for" className="mt-1.5" />
                  </div>
                  <div className="sm:col-span-2">
                    <Label>{t("percentageRange")}: {profile.desired_percentage_min}% – {profile.desired_percentage_max}%</Label>
                    <div className="grid grid-cols-2 gap-3 mt-2">
                      <Input type="number" min={20} max={80} value={profile.desired_percentage_min} onChange={(e) => setProfile({ ...profile, desired_percentage_min: Number(e.target.value) })} data-testid="emp-pct-min" />
                      <Input type="number" min={20} max={80} value={profile.desired_percentage_max} onChange={(e) => setProfile({ ...profile, desired_percentage_max: Number(e.target.value) })} data-testid="emp-pct-max" />
                    </div>
                  </div>
                  <div className="sm:col-span-2">
                    <Button type="submit" className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="emp-save-profile">{t("save")}</Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Suggested */}
          <TabsContent value="suggested" className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-xl font-semibold text-slate-900">{t("suggested")}</h2>
              <Button variant="outline" onClick={loadSuggested} disabled={loadingMatches} data-testid="refresh-matches-btn">
                {loadingMatches ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                {t("refreshMatches")}
              </Button>
            </div>
            {!hasProfile && (
              <Card><CardContent className="p-6 text-slate-500" data-testid="no-profile-hint">{t("noProfileYet")}</CardContent></Card>
            )}
            {loadingMatches && (
              <div className="text-center py-12 text-slate-500" data-testid="matches-loading">
                <Loader2 className="w-6 h-6 animate-spin mx-auto mb-3" />
                {t("computingMatch")}
              </div>
            )}
            {!loadingMatches && hasProfile && suggested.length === 0 && (
              <Card><CardContent className="p-6 text-slate-500" data-testid="no-suggested">{t("noJobs")}</CardContent></Card>
            )}
            <div className="grid gap-4">
              {suggested.map((j) => (
                <Card key={j.id} className="card-hover" data-testid={`job-card-${j.id}`}>
                  <CardContent className="p-6 flex gap-6 items-start">
                    <ScoreRing score={j.match_score || 0} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-display text-lg font-semibold text-slate-900">{j.title}</h3>
                        <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-50">{j.percentage_min}% – {j.percentage_max}%</Badge>
                        {j.location && <span className="text-xs text-slate-500 flex items-center gap-1"><MapPin className="w-3 h-3" />{j.location}</span>}
                      </div>
                      <div className="text-sm text-slate-500 mt-0.5">{j.company_name}</div>
                      <p className="text-sm text-slate-700 mt-3 leading-relaxed">{j.description}</p>
                      {j.match_reason && (
                        <div className="mt-3 text-xs text-slate-500"><span className="font-medium text-slate-700">{t("matchReason")}: </span>{j.match_reason}</div>
                      )}
                    </div>
                    <div>
                      {j.already_applied ? (
                        <Badge variant="secondary" data-testid={`applied-badge-${j.id}`}><CheckCircle2 className="w-3 h-3 mr-1" />{t("alreadyApplied")}</Badge>
                      ) : (
                        <Button onClick={() => apply(j.id)} className="bg-emerald-600 hover:bg-emerald-700 text-white" data-testid={`apply-btn-${j.id}`}>{t("apply")}</Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Applied */}
          <TabsContent value="applied" className="mt-6">
            <h2 className="font-display text-xl font-semibold text-slate-900 mb-4">{t("applied")}</h2>
            <div className="grid gap-4">
              {applications.length === 0 && <Card><CardContent className="p-6 text-slate-500" data-testid="no-applications">—</CardContent></Card>}
              {applications.map((a) => (
                <Card key={a.id} data-testid={`application-${a.id}`}>
                  <CardContent className="p-6 flex justify-between items-start gap-4">
                    <div>
                      <h3 className="font-display font-semibold text-slate-900">{a.job?.title || "—"}</h3>
                      <div className="text-sm text-slate-500">{a.job?.company_name}</div>
                      <div className="text-xs text-slate-500 mt-2">{new Date(a.applied_at).toLocaleString()}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{t("matchScore")}: {a.match_score || 0}</Badge>
                      <Badge variant="outline">{a.status}</Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
