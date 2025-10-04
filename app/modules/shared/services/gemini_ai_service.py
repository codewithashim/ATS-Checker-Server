import google.generativeai as genai
from typing import Dict, Any, List, Optional
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiAIService:
    def __init__(self):
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize Gemini AI model"""
        try:
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY not provided, AI features will be disabled")
                return
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            logger.info(f"Initialized Gemini AI model: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.model = None

    async def analyze_resume_ats(self, resume_content: str, job_description: str = None) -> Dict[str, Any]:
        """Analyze resume for ATS compatibility using Gemini AI"""
        if not self.model:
            return self._get_fallback_analysis(resume_content, job_description)

        try:
            prompt = self._create_ats_analysis_prompt(resume_content, job_description)
            response = await self._generate_content(prompt)
            return self._parse_ats_response(response)
        except Exception as e:
            logger.error(f"Gemini AI analysis failed: {e}")
            return self._get_fallback_analysis(resume_content, job_description)

    async def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text using Gemini AI"""
        if not self.model:
            return self._extract_keywords_fallback(text, max_keywords)

        try:
            prompt = f"""
            Extract the most important keywords from the following text. 
            Return only a JSON array of {max_keywords} keywords, no other text.
            
            Text: {text[:2000]}
            """
            
            response = await self._generate_content(prompt)
            keywords = json.loads(response.strip())
            return keywords[:max_keywords] if isinstance(keywords, list) else []
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return self._extract_keywords_fallback(text, max_keywords)

    async def improve_resume_suggestions(self, resume_content: str, job_description: str = None) -> Dict[str, Any]:
        """Get AI-powered suggestions to improve resume"""
        if not self.model:
            return self._get_fallback_suggestions(resume_content, job_description)

        try:
            prompt = self._create_improvement_prompt(resume_content, job_description)
            response = await self._generate_content(prompt)
            return self._parse_improvement_response(response)
        except Exception as e:
            logger.error(f"Resume improvement suggestions failed: {e}")
            return self._get_fallback_suggestions(resume_content, job_description)

    async def match_resume_to_job(self, resume_content: str, job_description: str) -> Dict[str, Any]:
        """Match resume against job description using AI"""
        if not self.model:
            return self._get_fallback_match(resume_content, job_description)

        try:
            prompt = self._create_job_match_prompt(resume_content, job_description)
            response = await self._generate_content(prompt)
            return self._parse_job_match_response(response)
        except Exception as e:
            logger.error(f"Job matching failed: {e}")
            return self._get_fallback_match(resume_content, job_description)

    def _create_ats_analysis_prompt(self, resume_content: str, job_description: str = None) -> str:
        """Create prompt for ATS analysis"""
        base_prompt = """
        As an expert ATS (Applicant Tracking System) analyst, analyze the following resume for ATS compatibility.
        
        Please provide a comprehensive analysis in the following JSON format:
        {
            "overall_score": 85,
            "ats_checks": {
                "contact_info": true,
                "skills_section": true,
                "experience_section": true,
                "education_section": true,
                "quantifiable_achievements": true,
                "standard_formatting": true,
                "action_verbs": true,
                "appropriate_length": true,
                "no_graphics": true,
                "standard_fonts": true
            },
            "strengths": ["List of strengths"],
            "weaknesses": ["List of weaknesses"],
            "recommendations": [
                {
                    "category": "Formatting",
                    "priority": "High",
                    "suggestion": "Use standard fonts like Arial or Times New Roman",
                    "impact": "Improves ATS parsing accuracy"
                }
            ],
            "keyword_analysis": {
                "missing_keywords": ["keyword1", "keyword2"],
                "present_keywords": ["keyword3", "keyword4"],
                "keyword_density": 0.15
            }
        }
        
        Resume Content:
        """
        
        if job_description:
            base_prompt += f"""
            
            Job Description (for keyword matching):
            {job_description[:1000]}
            """
        
        base_prompt += f"""
        
        {resume_content[:3000]}
        
        Provide only the JSON response, no additional text.
        """
        
        return base_prompt

    def _create_improvement_prompt(self, resume_content: str, job_description: str = None) -> str:
        """Create prompt for resume improvement suggestions"""
        prompt = f"""
        As a professional resume writer and career coach, provide specific suggestions to improve this resume.
        
        Resume Content:
        {resume_content[:2000]}
        """
        
        if job_description:
            prompt += f"""
            
            Target Job Description:
            {job_description[:1000]}
            """
        
        prompt += """
        
        Provide suggestions in this JSON format:
        {
            "overall_rating": 7,
            "sections": {
                "summary": {
                    "current": "Brief description of current summary",
                    "suggested": "Improved summary suggestion",
                    "reason": "Why this improvement helps"
                },
                "experience": {
                    "current": "Current experience section issues",
                    "suggested": "How to improve experience descriptions",
                    "reason": "Impact on ATS and recruiter appeal"
                },
                "skills": {
                    "current": "Current skills section analysis",
                    "suggested": "Skills section improvements",
                    "reason": "Better keyword optimization"
                }
            },
            "action_items": [
                {
                    "action": "Add quantifiable achievements",
                    "priority": "High",
                    "example": "Increased sales by 25% over 6 months"
                }
            ]
        }
        
        Provide only the JSON response.
        """
        
        return prompt

    def _create_job_match_prompt(self, resume_content: str, job_description: str) -> str:
        """Create prompt for job matching analysis"""
        return f"""
        Analyze how well this resume matches the job description.
        
        Resume:
        {resume_content[:2000]}
        
        Job Description:
        {job_description[:1500]}
        
        Provide analysis in this JSON format:
        {{
            "match_score": 75,
            "required_skills_match": 0.8,
            "experience_match": 0.7,
            "education_match": 0.9,
            "missing_requirements": ["skill1", "experience2"],
            "strengths": ["strength1", "strength2"],
            "recommendations": [
                "Add experience with [specific technology]",
                "Highlight [specific achievement]"
            ],
            "keyword_matches": {{
                "found": ["keyword1", "keyword2"],
                "missing": ["keyword3", "keyword4"]
            }}
        }}
        
        Provide only the JSON response.
        """

    async def _generate_content(self, prompt: str) -> str:
        """Generate content using Gemini AI"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini AI generation failed: {e}")
            raise

    def _parse_ats_response(self, response: str) -> Dict[str, Any]:
        """Parse ATS analysis response from Gemini"""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse ATS response: {e}")
            return self._get_fallback_analysis("", "")

    def _parse_improvement_response(self, response: str) -> Dict[str, Any]:
        """Parse improvement suggestions response"""
        try:
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse improvement response: {e}")
            return self._get_fallback_suggestions("", "")

    def _parse_job_match_response(self, response: str) -> Dict[str, Any]:
        """Parse job match response"""
        try:
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse job match response: {e}")
            return self._get_fallback_match("", "")

    def _get_fallback_analysis(self, resume_content: str, job_description: str = None) -> Dict[str, Any]:
        """Fallback analysis when AI is not available"""
        return {
            "overall_score": 70,
            "ats_checks": {
                "contact_info": bool(resume_content and '@' in resume_content),
                "skills_section": 'skills' in resume_content.lower(),
                "experience_section": 'experience' in resume_content.lower(),
                "education_section": 'education' in resume_content.lower(),
                "quantifiable_achievements": any(char.isdigit() for char in resume_content),
                "standard_formatting": len(resume_content.split('\n')) > 10,
                "action_verbs": any(verb in resume_content.lower() for verb in 
                    ['managed', 'led', 'developed', 'created', 'implemented', 'achieved']),
                "appropriate_length": 200 <= len(resume_content) <= 2000,
                "no_graphics": True,
                "standard_fonts": True
            },
            "strengths": ["Basic structure present"],
            "weaknesses": ["AI analysis unavailable"],
            "recommendations": [
                {
                    "category": "General",
                    "priority": "Medium",
                    "suggestion": "Enable AI analysis for detailed feedback",
                    "impact": "Provides comprehensive ATS optimization"
                }
            ],
            "keyword_analysis": {
                "missing_keywords": [],
                "present_keywords": [],
                "keyword_density": 0.0
            }
        }

    def _get_fallback_suggestions(self, resume_content: str, job_description: str = None) -> Dict[str, Any]:
        """Fallback suggestions when AI is not available"""
        return {
            "overall_rating": 6,
            "sections": {
                "summary": {
                    "current": "Basic summary present",
                    "suggested": "Add quantifiable achievements",
                    "reason": "Improves ATS scoring"
                }
            },
            "action_items": [
                {
                    "action": "Enable AI analysis",
                    "priority": "High",
                    "example": "Get detailed AI-powered suggestions"
                }
            ]
        }

    def _get_fallback_match(self, resume_content: str, job_description: str) -> Dict[str, Any]:
        """Fallback job matching when AI is not available"""
        return {
            "match_score": 60,
            "required_skills_match": 0.5,
            "experience_match": 0.5,
            "education_match": 0.5,
            "missing_requirements": ["AI analysis required"],
            "strengths": ["Basic resume structure"],
            "recommendations": ["Enable AI analysis for accurate matching"],
            "keyword_matches": {
                "found": [],
                "missing": []
            }
        }

    def _extract_keywords_fallback(self, text: str, max_keywords: int) -> List[str]:
        """Fallback keyword extraction"""
        # Simple keyword extraction based on word frequency
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3 and word.isalpha():
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]

# Global instance
gemini_ai_service = GeminiAIService()
