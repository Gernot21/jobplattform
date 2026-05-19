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
import { Trash2, Users, MapPin, Plus } from "lucide-react";

export default function EmployerDashboard() {
  const { t } = useI18n();
  const [tab, setTab] = useState("profile");

  const [profile, setProfile] = useState({
    company_name: "",
    company_description: "",
    contact_person: "",
    contact_email: "",
  });
  const [hasProfile, setHasProfile] = useState(false);

  const [jobs, setJobs] = useState([]);
  const [newJob, setNewJob] = useState({
    title: "",
    description: "",
    percentage_min: 20,
    percentage_max: 80,
    location: "",
  });

  const [openApplicantsFor, setOpenApplicantsFor] = useState(null);
  const [applicants, setApplicants] = useState([]);

  useEffect(() => {
    loadProfile();
    loadJobs();
  }, []);

  const loadProfile = async () => {
    const { data } = await api.get("/employer/profile");
    if (data && data.company_name) {
      setProfile({ ...profile, ...data });
      setHasProfile(true);
    }
  };

  const loadJobs = async () => {
    const { data } = await api.get("/employer/jobs");
    setJobs(data);
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    try {
      await api.put("/employer/profile", profile);
      setHasProfile(true);
      toast.success("Profil gespeichert");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Fehler");
    }
  };

  const createJob = async (e) => {
    e.preventDefault();
    try {
      await api.post("/employer/jobs", newJob);
      toast.success("Stelle veröffentlicht");
      setNewJob({ title: "", description: "", percentage_min: 20, percentage_max: 80, location: "" });
      loadJobs();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Fehler");
    }
  };

  const deleteJob = async (id) => {
    if (!confirm(t("delete_confirm"))) return;
    await api.delete(`/employer/jobs/${id}`);
    loadJobs();
    if (openApplicantsFor === id) setOpenApplicantsFor(null);
  };

  const openApplicants = async (id) => {
    if (openApplicantsFor === id) {
      setOpenApplicantsFor(null);
      return;
    }
    const { data } = await api.get(`/employer/jobs/${id}/applicants`);
    setApplicants(data);
    setOpenApplicantsFor(id);
  };

  return (
    <div className="min-h-screen">
      <Header title={t("employer")} />
      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8" data-testid="employer-dashboard">
        <h1 className="font-display text-3xl font-bold text-slate-900 mb-1">{t("welcome")}</h1>
        <p className="text-slate-500 mb-8">{t("subtagline")}</p>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="bg-white border border-slate-200 p-1">
            <TabsTrigger value="profile" data-testid="empr-tab-profile">{t("profile")}</TabsTrigger>
            <TabsTrigger value="jobs" data-testid="empr-tab-jobs">{t("myJobs")}</TabsTrigger>
          </TabsList>

          {/* Profile */}
          <TabsContent value="profile" className="mt-6">
            <Card>
              <CardHeader><CardTitle className="font-display">{t("profile")}</CardTitle></CardHeader>
              <CardContent>
                <form onSubmit={saveProfile} className="grid sm:grid-cols-2 gap-5">
                  <div className="sm:col-span-2">
                    <Label>{t("companyName")}</Label>
                    <Input value={profile.company_name} onChange={(e) => setProfile({ ...profile, company_name: e.target.value })} required data-testid="empr-company-name" className="mt-1.5" />
                  </div>
                  <div className="sm:col-span-2">
                    <Label>{t("companyDescription")}</Label>
                    <Textarea value={profile.company_description} onChange={(e) => setProfile({ ...profile, company_description: e.target.value })} rows={4} required data-testid="empr-company-description" className="mt-1.5" />
                  </div>
                  <div>
                    <Label>{t("contactPerson")}</Label>
                    <Input value={profile.contact_person} onChange={(e) => setProfile({ ...profile, contact_person: e.target.value })} required data-testid="empr-contact-person" className="mt-1.5" />
                  </div>
                  <div>
                    <Label>{t("contactEmail")}</Label>
                    <Input type="email" value={profile.contact_email} onChange={(e) => setProfile({ ...profile, contact_email: e.target.value })} required data-testid="empr-contact-email" className="mt-1.5" />
                  </div>
                  <div className="sm:col-span-2">
                    <Button type="submit" className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="empr-save-profile">{t("save")}</Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Jobs */}
          <TabsContent value="jobs" className="mt-6 space-y-6">
            {!hasProfile && (
              <Card><CardContent className="p-6 text-slate-500" data-testid="empr-no-profile">{t("noProfileYet")}</CardContent></Card>
            )}

            {hasProfile && (
              <Card>
                <CardHeader><CardTitle className="font-display flex items-center gap-2"><Plus className="w-5 h-5 text-emerald-600" />{t("createJob")}</CardTitle></CardHeader>
                <CardContent>
                  <form onSubmit={createJob} className="grid sm:grid-cols-2 gap-5">
                    <div className="sm:col-span-2">
                      <Label>{t("jobTitle")}</Label>
                      <Input value={newJob.title} onChange={(e) => setNewJob({ ...newJob, title: e.target.value })} required data-testid="job-title-input" className="mt-1.5" />
                    </div>
                    <div className="sm:col-span-2">
                      <Label>{t("jobDescription")}</Label>
                      <Textarea value={newJob.description} onChange={(e) => setNewJob({ ...newJob, description: e.target.value })} rows={5} required data-testid="job-description-input" className="mt-1.5" />
                    </div>
                    <div>
                      <Label>{t("location")}</Label>
                      <Input value={newJob.location} onChange={(e) => setNewJob({ ...newJob, location: e.target.value })} data-testid="job-location-input" className="mt-1.5" />
                    </div>
                    <div>
                      <Label>{t("percentage")} (20% – 80%)</Label>
                      <div className="grid grid-cols-2 gap-2 mt-1.5">
                        <Input type="number" min={20} max={80} value={newJob.percentage_min} onChange={(e) => setNewJob({ ...newJob, percentage_min: Number(e.target.value) })} data-testid="job-pct-min" />
                        <Input type="number" min={20} max={80} value={newJob.percentage_max} onChange={(e) => setNewJob({ ...newJob, percentage_max: Number(e.target.value) })} data-testid="job-pct-max" />
                      </div>
                    </div>
                    <div className="sm:col-span-2">
                      <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white" data-testid="job-publish-btn">{t("createJob")}</Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            <div className="space-y-3">
              {jobs.map((j) => (
                <Card key={j.id} className="card-hover" data-testid={`empr-job-${j.id}`}>
                  <CardContent className="p-5">
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-display text-lg font-semibold text-slate-900">{j.title}</h3>
                          <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{j.percentage_min}% – {j.percentage_max}%</Badge>
                          {j.location && <span className="text-xs text-slate-500 flex items-center gap-1"><MapPin className="w-3 h-3" />{j.location}</span>}
                        </div>
                        <p className="text-sm text-slate-600 mt-2 line-clamp-2">{j.description}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => openApplicants(j.id)} data-testid={`view-applicants-${j.id}`}>
                          <Users className="w-4 h-4 mr-1.5" />{t("applicants")}
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => deleteJob(j.id)} data-testid={`delete-job-${j.id}`}>
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </div>
                    </div>

                    {openApplicantsFor === j.id && (
                      <div className="mt-5 border-t border-slate-200 pt-5" data-testid={`applicants-panel-${j.id}`}>
                        <h4 className="font-medium text-slate-900 mb-3">{t("applicants")} ({applicants.length})</h4>
                        {applicants.length === 0 && <div className="text-sm text-slate-500">—</div>}
                        <div className="space-y-2">
                          {applicants.map((a) => (
                            <div key={a.id} className="flex justify-between items-start bg-slate-50 rounded-md p-3" data-testid={`applicant-${a.id}`}>
                              <div className="flex-1">
                                <div className="font-medium text-slate-900">
                                  {a.profile?.first_name} {a.profile?.last_name}
                                </div>
                                <div className="text-xs text-slate-500">{a.email}</div>
                                {a.profile?.core_skills && (
                                  <div className="text-xs text-slate-600 mt-1.5"><span className="font-medium">{t("coreSkills")}:</span> {a.profile.core_skills}</div>
                                )}
                                {a.profile?.looking_for && (
                                  <div className="text-xs text-slate-600 mt-1"><span className="font-medium">{t("lookingFor")}:</span> {a.profile.looking_for}</div>
                                )}
                                {a.cover_letter && (
                                  <div className="text-xs text-slate-600 mt-1 italic">"{a.cover_letter}"</div>
                                )}
                              </div>
                              <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{t("matchScore")}: {a.match_score || 0}</Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
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
