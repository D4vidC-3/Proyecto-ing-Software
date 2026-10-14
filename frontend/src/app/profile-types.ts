export type WorkExperience = {
  company: string | null;
  role: string | null;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
};

export type Education = {
  degree: string | null;
  institution: string | null;
  start_year: number | null;
  end_year: number | null;
};

export type CandidateProfile = {
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  professional_summary: string | null;
  target_role: string | null;
  years_experience: number | null;
  skills: string[];
  languages: string[];
  work_experience: WorkExperience[];
  education: Education[];
  preferences: {
    desired_roles: string[];
    preferred_locations: string[];
    work_modes: string[];
    salary_min_cop: number | null;
    salary_max_cop: number | null;
    contract_type: string | null;
    availability: string | null;
  };
};
