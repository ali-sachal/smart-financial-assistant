from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Contact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    linkedin: Optional[str] = None

class SkillItem(BaseModel):
    id: Optional[str] = None
    category: Optional[str] = None
    items: List[str] = []

class EducationItem(BaseModel):
    id: Optional[str] = None
    degree: Optional[str] = None
    institute: Optional[str] = None
    fieldOfStudy: Optional[str] = None
    grade: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    achievements: List[str] = []

class ExperienceItem(BaseModel):
    id: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    description: List[str] = []
    certificateLink: Optional[str] = None

class ProjectItem(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    link: Optional[str] = None
    problemStatement: List[str] = []

class ActivityItem(BaseModel):
    id: Optional[str] = None
    role: Optional[str] = None
    association: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    accomplishments: List[str] = []

class AwardItem(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    host: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    letterLink: Optional[str] = None

class CertificationItem(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    authority: Optional[str] = None
    link: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class CustomSectionItemDetail(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    description: List[str] = []

class CustomSection(BaseModel):
    id: Optional[str] = None
    sectionTitle: Optional[str] = None
    items: List[CustomSectionItemDetail] = []

class SectionTitles(BaseModel):
    personal: Optional[str] = "Personal details"
    summary: Optional[str] = "Professional Summary"
    education: Optional[str] = "Education"
    projects: Optional[str] = "Projects"
    skills: Optional[str] = "Technical Proficiencies"
    certifications: Optional[str] = "Certifications"
    links: Optional[str] = "Websites & Social Links"
    experience: Optional[str] = "Employment History"
    activities: Optional[str] = "Extra-Curricular & Leadership"
    awards: Optional[str] = "Awards & Scholarships"

class ResumeParsed(BaseModel):
    uuid: Optional[str] = None
    user_id: Optional[str] = None
    contact: Contact
    summary: Optional[str] = ""
    skills: List[SkillItem]
    education: List[EducationItem]
    experience: List[ExperienceItem]
    projects: List[ProjectItem]
    activities: List[ActivityItem] = []
    awards: List[AwardItem] = []
    certifications: List[CertificationItem] = []
    customSections: List[CustomSection] = []
    sectionTitles: SectionTitles = Field(default_factory=SectionTitles)
    sectionOrder: List[str] = []
    llm_data: Optional[Dict[str, Any]] = Field(None, description="The complete raw response data from the LLM, including usage metadata")