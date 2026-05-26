// User Types
export type UserRole = 'employee' | 'employer' | 'superuser'
export type EmploymentType = 'job' | 'freelancer' | 'shared_job'
export type EmploymentStatus = 'full_time' | 'part_time' | 'contract'

export interface User {
  id: string
  email: string
  role: UserRole
  created_at: string
  updated_at: string
}

export interface EmployeeProfile extends User {
  first_name: string
  last_name: string
  cv_url?: string
  core_competencies: string[]
  important_experience: string
  usp: string
  looking_for: EmploymentType[]
  desired_pensum: number
  location: string
  salary_expectation_min: number
  salary_expectation_max: number
  premium: boolean
  premium_until?: string
}

export interface EmployerProfile extends User {
  company_name: string
  company_description: string
  industry: string
  contact_person: string
  contact_email: string
  contact_phone: string
  family_friendly_questions: string[]
  verified: boolean
}

export interface JobPosting {
  id: string
  employer_id: string
  position_name: string
  employment_type: EmploymentType
  required_pensum: number
  required_competencies: string[]
  required_experience: string
  salary_min: number
  salary_max: number
  salary_type: 'per_year' | 'per_month' | 'per_project'
  location: string
  description: string
  pdf_url?: string
  external_application_url?: string
  created_at: string
  updated_at: string
  status: 'active' | 'closed' | 'draft'
}

export interface Application {
  id: string
  job_id: string
  employee_id: string
  status: 'pending' | 'viewed' | 'accepted' | 'rejected' | 'withdrawn'
  cover_letter: string
  applied_at: string
  responded_at?: string
}

export interface JobMatch {
  job_id: string
  employee_id: string
  match_score: number
  matched_at: string
}

export interface Message {
  id: string
  sender_id: string
  receiver_id: string
  content: string
  attachments?: string[]
  created_at: string
  read_at?: string
}

export interface Feedback {
  id: string
  user_id: string
  type: 'bug' | 'feature' | 'design' | 'general'
  title: string
  description: string
  created_at: string
}

export interface Subscription {
  id: string
  user_id: string
  tier: 'free' | 'basic' | 'pro' | 'enterprise'
  stripe_customer_id: string
  stripe_subscription_id?: string
  amount: number
  currency: string
  status: 'active' | 'cancelled' | 'expired'
  current_period_start: string
  current_period_end: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}