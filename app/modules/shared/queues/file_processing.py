import asyncio
import os
import aiofiles
from typing import Dict, Any
from beanie import PydanticObjectId
from app.core.queue import queue_manager
from app.modules.resume.models import Resume, ResumeAnalysis
from app.modules.resume.services import ResumeAnalysisService
from app.modules.shared.services.gemini_ai_service import gemini_ai_service
import logging

logger = logging.getLogger(__name__)

class FileProcessingQueue:
    QUEUE_NAME = "file_processing"
    
    @staticmethod
    async def add_file_processing_job(
        resume_id: str,
        file_path: str,
        analysis_type: str = "ats_check",
        job_posting_id: str = None
    ):
        """Add a file processing job to the queue"""
        job_data = {
            "resume_id": resume_id,
            "file_path": file_path,
            "analysis_type": analysis_type,
            "job_posting_id": job_posting_id,
            "created_at": asyncio.get_event_loop().time()
        }
        
        await queue_manager.add_job(
            FileProcessingQueue.QUEUE_NAME,
            job_data,
            {"priority": 1, "delay": 0}
        )
        logger.info(f"Added file processing job for resume {resume_id}")

    @staticmethod
    async def process_file(job_data: Dict[str, Any]):
        """Process a file from the queue"""
        resume_id = job_data.get("resume_id")
        file_path = job_data.get("file_path")
        analysis_type = job_data.get("analysis_type", "ats_check")
        job_posting_id = job_data.get("job_posting_id")
        
        try:
            logger.info(f"Processing file for resume {resume_id}")
            
            # Extract text from file
            content = await FileProcessingQueue.extract_text_from_file(file_path)
            
            # Update resume with extracted content
            resume = await Resume.get(PydanticObjectId(resume_id))
            if resume:
                await resume.update({"$set": {"content": content}})
                logger.info(f"Updated resume {resume_id} with extracted content")
            
            # Create analysis record
            analysis_data = {
                "resume_id": PydanticObjectId(resume_id),
                "job_posting_id": PydanticObjectId(job_posting_id) if job_posting_id else None,
                "analysis_type": analysis_type,
                "score": 0,
                "details": {},
                "recommendations": {}
            }
            
            analysis = await ResumeAnalysisService.create_analysis(analysis_data)
            
            # Perform AI-powered ATS analysis
            await FileProcessingQueue.perform_ai_ats_analysis(analysis, content, job_posting_id)
            
            logger.info(f"Successfully processed file for resume {resume_id}")
            
        except Exception as e:
            logger.error(f"Failed to process file for resume {resume_id}: {e}")
            raise

    @staticmethod
    async def extract_text_from_file(file_path: str) -> str:
        """Extract text from uploaded file based on file type"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return await FileProcessingQueue.extract_text_from_pdf(file_path)
            elif file_extension in ['.doc', '.docx']:
                return await FileProcessingQueue.extract_text_from_word(file_path)
            elif file_extension == '.txt':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to extract text from file {file_path}: {e}")
            return ""

    @staticmethod
    async def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            # In production, you would use PyPDF2 or pdfplumber
            # For now, return a placeholder
            logger.info(f"Extracting text from PDF: {file_path}")
            return "PDF content extracted - placeholder text"
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            return ""

    @staticmethod
    async def extract_text_from_word(file_path: str) -> str:
        """Extract text from Word document"""
        try:
            # In production, you would use python-docx
            # For now, return a placeholder
            logger.info(f"Extracting text from Word document: {file_path}")
            return "Word document content extracted - placeholder text"
        except Exception as e:
            logger.error(f"Failed to extract text from Word document {file_path}: {e}")
            return ""

    @staticmethod
    async def perform_ai_ats_analysis(analysis: ResumeAnalysis, content: str, job_posting_id: str = None):
        """Perform AI-powered ATS analysis on resume content"""
        try:
            # Get job description if available
            job_description = None
            if job_posting_id:
                from app.modules.job_posting.models import JobPosting
                job_posting = await JobPosting.get(PydanticObjectId(job_posting_id))
                if job_posting:
                    job_description = f"{job_posting.title} - {job_posting.description}"
            
            # Use Gemini AI for comprehensive analysis
            ai_analysis = await gemini_ai_service.analyze_resume_ats(content, job_description)
            
            # Extract keywords using AI
            keywords = await gemini_ai_service.extract_keywords(content)
            
            # Get improvement suggestions
            suggestions = await gemini_ai_service.improve_resume_suggestions(content, job_description)
            
            # Update analysis with AI results
            await ResumeAnalysisService.update_analysis(
                analysis.id,
                {
                    "score": ai_analysis.get("overall_score", 70),
                    "details": {
                        'ats_checks': ai_analysis.get("ats_checks", {}),
                        'strengths': ai_analysis.get("strengths", []),
                        'weaknesses': ai_analysis.get("weaknesses", []),
                        'keyword_analysis': ai_analysis.get("keyword_analysis", {}),
                        'content_length': len(content),
                        'word_count': len(content.split()),
                        'extracted_keywords': keywords,
                        'ai_suggestions': suggestions
                    },
                    "recommendations": {
                        'ai_recommendations': ai_analysis.get("recommendations", []),
                        'improvement_suggestions': suggestions.get("action_items", []),
                        'priority': ai_analysis.get("recommendations", [])[:3]
                    }
                }
            )
            
            logger.info(f"Completed AI-powered ATS analysis for resume {analysis.resume_id} with score {ai_analysis.get('overall_score', 70)}")
            
        except Exception as e:
            logger.error(f"Failed to perform AI ATS analysis: {e}")
            # Fallback to basic analysis
            await FileProcessingQueue.perform_basic_ats_analysis(analysis, content, job_posting_id)

    @staticmethod
    async def perform_basic_ats_analysis(analysis: ResumeAnalysis, content: str, job_posting_id: str = None):
        """Fallback basic ATS analysis when AI is not available"""
        try:
            # Basic ATS analysis logic
            ats_checks = {
                'has_contact_info': bool(content and '@' in content),
                'has_skills_section': 'skills' in content.lower(),
                'has_experience_section': 'experience' in content.lower(),
                'has_education_section': 'education' in content.lower(),
                'has_quantifiable_achievements': any(char.isdigit() for char in content),
                'uses_standard_formatting': len(content.split('\n')) > 10,
                'has_action_verbs': any(verb in content.lower() for verb in 
                    ['managed', 'led', 'developed', 'created', 'implemented', 'achieved']),
                'appropriate_length': 200 <= len(content) <= 2000
            }
            
            # Calculate score
            passed_checks = sum(ats_checks.values())
            score = int((passed_checks / len(ats_checks)) * 100)
            
            # Generate recommendations
            recommendations = []
            if not ats_checks['has_contact_info']:
                recommendations.append("Add clear contact information at the top")
            if not ats_checks['has_skills_section']:
                recommendations.append("Include a dedicated skills section")
            if not ats_checks['has_quantifiable_achievements']:
                recommendations.append("Add quantifiable achievements with numbers")
            if not ats_checks['uses_standard_formatting']:
                recommendations.append("Use clear section headers and bullet points")
            if not ats_checks['has_action_verbs']:
                recommendations.append("Use strong action verbs to describe achievements")
            if not ats_checks['appropriate_length']:
                recommendations.append("Adjust resume length to be between 1-2 pages")
            
            # Update analysis with results
            await ResumeAnalysisService.update_analysis(
                analysis.id,
                {
                    "score": score,
                    "details": {
                        'ats_checks': ats_checks,
                        'content_length': len(content),
                        'word_count': len(content.split())
                    },
                    "recommendations": {
                        'general': recommendations,
                        'priority': recommendations[:3]
                    }
                }
            )
            
            logger.info(f"Completed basic ATS analysis for resume {analysis.resume_id} with score {score}")
            
        except Exception as e:
            logger.error(f"Failed to perform basic ATS analysis: {e}")
            raise
