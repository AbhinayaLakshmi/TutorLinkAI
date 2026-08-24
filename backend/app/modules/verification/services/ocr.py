import os
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("ocr_service")

# Try to import PaddleOCR. Handle failure gracefully if the library is not installed or missing platform builds.
PADDLE_AVAILABLE = False
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    logger.warning("PaddleOCR library not installed. Falling back to stub mode.")

class CertificateOCR:
    def __init__(self):
        self.ocr_instance = None
        self._initialized = False
        self.line_confidences = {}  # Map of extracted line text -> OCR confidence score

    def _initialize(self):
        if self._initialized:
            return
        if PADDLE_AVAILABLE:
            try:
                # Initialize PaddleOCR (downloads models on demand first time)
                # use_textline_orientation is the current parameter replacing use_angle_cls
                # show_log parameter is removed as it's unsupported in newer versions
                self.ocr_instance = PaddleOCR(use_textline_orientation=True, lang="en")
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR engine: {str(e)}")
                self.ocr_instance = None
        else:
            logger.info("PaddleOCR engine not loaded (library unavailable).")

    def extract_text_from_file(self, file_path: str) -> List[str]:
        """
        Executes raw OCR text detection on the document.
        Returns a list of strings found in the file.
        """
        self._initialize()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Certificate file not found on disk at {file_path}")

        # Return empty text if OCR engine is unavailable
        if not self.ocr_instance:
            logger.warning(f"OCR engine unavailable. Cannot extract text from: {file_path}")
            return []

        try:
            # Clear previous confidences cache
            self.line_confidences = {}
            # Newer paddleocr version: results is list of dicts (one per page) containing 'rec_texts' and 'rec_scores'
            # Older paddleocr version: results is [[ [box, (text, confidence)], ... ]]
            results = self.ocr_instance.ocr(file_path)
            text_lines = []
            if results:
                for page in results:
                    if isinstance(page, dict) and "rec_texts" in page:
                        texts = page["rec_texts"]
                        scores = page.get("rec_scores", [1.0] * len(texts))
                        for text, score in zip(texts, scores):
                            text_lines.append(text)
                            self.line_confidences[text.strip()] = float(score)
                    elif isinstance(page, list):
                        for line in page:
                            if line:
                                for word_info in line:
                                    text = word_info[1][0]
                                    score = word_info[1][1]
                                    text_lines.append(text)
                                    self.line_confidences[text.strip()] = float(score)
            return text_lines
        except Exception as e:
            logger.error(f"Error executing PaddleOCR on file {file_path}: {str(e)}")
            return []

    def parse_metadata(self, text_lines: List[str]) -> Dict[str, Any]:
        """
        Parses raw text lines to search for standard credential properties:
        - University name
        - Candidate name
        - Degree level/title
        - Graduation year
        
        Uses heuristic string lookups.
        """
        clean_text_block = " ".join(text_lines)
        
        # 1. Parse University / Institution Candidate
        university = None
        source_uni_line = None
        
        # Look for Syndicate/Senate of the <University>
        syndicate_match = re.search(
            r"\b(?:Syndicate\s+of\s+the|Syndicate\s+of|Senate\s+of\s+the|Senate\s+of|University\s+of)\s+([A-Z][a-zA-Z\s\.\-]{3,50}?)\b\s*(?:hereby|makes|conferred|granted|admits)\b",
            clean_text_block,
            re.IGNORECASE
        )
        if syndicate_match:
            university = syndicate_match.group(1).strip()
            # Find which line it came from
            for line in text_lines:
                if university.lower() in line.lower():
                    source_uni_line = line
                    break
        
        if not university:
            # Look for "<Name> University"
            uni_match = re.search(r"\b([A-Z][A-Za-z\s\.\-]{3,50}?\s+University)\b", clean_text_block)
            if uni_match:
                university = uni_match.group(1).strip()
                for line in text_lines:
                    if university.lower() in line.lower():
                        source_uni_line = line
                        break
            else:
                # Look for "University of <Name>"
                uni_match = re.search(r"\b(University\s+of\s+[A-Z][A-Za-z\s\.\-]{3,50}?)\b", clean_text_block, re.IGNORECASE)
                if uni_match:
                    university = uni_match.group(1).strip()
                    for line in text_lines:
                        if university.lower() in line.lower():
                            source_uni_line = line
                            break

        # Check for adjacent lines combination (e.g. "University" + "Anna")
        if not university:
            for idx, line in enumerate(text_lines):
                line_clean = line.strip()
                if line_clean.lower() == "university" and idx + 1 < len(text_lines):
                    next_line = text_lines[idx + 1].strip()
                    if next_line.lower() == "anna":
                        university = "Anna University"
                        source_uni_line = f"{line} {text_lines[idx+1]}"
                        break
                elif line_clean.lower() == "anna" and idx + 1 < len(text_lines):
                    next_line = text_lines[idx + 1].strip()
                    if next_line.lower() == "university":
                        university = "Anna University"
                        source_uni_line = f"{line} {text_lines[idx+1]}"
                        break

        # If still not found, fallback to any line containing "university" that isn't just a generic single word
        if not university:
            for line in text_lines:
                line_clean = line.strip()
                if len(line_clean.split()) > 1 and re.search(r"\b(university|college|institute|academy|school of)\b", line_clean, re.IGNORECASE):
                    university = line_clean
                    source_uni_line = line
                    break

        # Clean up university
        if university:
            university = university.strip(",. ").title()
            
        # 2. Parse Graduation Year
        year = None
        source_year_line = None
        years_found = []
        for idx, line in enumerate(text_lines):
            matches = re.findall(r"\b([12]\d{3})\b", line)
            for y in matches:
                y_val = int(y)
                if not (1950 <= y_val <= 2030):
                    continue
                score = 0
                context_window = ""
                if idx > 0:
                    context_window += text_lines[idx - 1] + " "
                context_window += line + " "
                if idx + 1 < len(text_lines):
                    context_window += text_lines[idx + 1]
                
                if re.search(r"\b(examination\s+held\s+in|held\s+in|passed\s+in|completed\s+in|graduated\s+in|degree\s+conferred|examination|held)\b", context_window, re.IGNORECASE):
                    score += 50
                if re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", context_window, re.IGNORECASE):
                    score += 10
                if re.search(r"\b(date\s+of\s+issue|issued|dated|seal|signed|registrar|controller|vice-chancellor)\b", context_window, re.IGNORECASE):
                    score -= 20
                years_found.append((y_val, score, line))

        if years_found:
            years_found.sort(key=lambda x: (-x[1], x[0]))
            year = years_found[0][0]
            source_year_line = years_found[0][2]

        # 3. Parse Degree
        degree = None
        source_deg_line = None
        degree_keywords = [
            "Bachelor", "Master", "Doctor", "PhD", "B.Sc", "B.A", "M.Sc", "M.A", "MBA", "B.Tech", "M.Tech", "Diploma"
        ]
        for idx, line in enumerate(text_lines):
            line_clean = line.strip()
            level_match = re.search(r"\b(Bachelor|Master|Doctor|Diploma|B\.?Sc|B\.?A|M\.?Sc|M\.?A|MBA|B\.?Tech|M\.?Tech|Ph\.?D)\b", line_clean, re.IGNORECASE)
            if level_match:
                level = level_match.group(1).title()
                if level.lower().startswith("ph"):
                    level = "Doctor of Philosophy"
                
                # Check for line-ending designation (split across lines)
                match_end = re.search(r"\b(Bachelor|Master|Doctor|Diploma)\s+(of|in)\s*$", line_clean, re.IGNORECASE)
                if match_end and idx + 1 < len(text_lines):
                    next_line = text_lines[idx + 1].strip()
                    next_match = re.match(r"^([A-Za-z\s\-]+?)\s+(?:in|under|with|at|having|completed|of)\b", next_line, re.IGNORECASE)
                    if next_match:
                        degree = f"{level} of {next_match.group(1).strip()}"
                        source_deg_line = f"{line} {text_lines[idx + 1]}"
                        break
                    else:
                        words = next_line.split()
                        if words and len(words) <= 3:
                            degree = f"{level} of {words[0]}"
                            source_deg_line = f"{line} {text_lines[idx + 1]}"
                            break

                # Check if same line contains "Bachelor/Master of <Major>"
                match_same = re.search(r"\b(Bachelor|Master|Doctor|Diploma)\s+(of|in)\s+([A-Za-z\s\-]{3,30}?)\b(?:in|under|having|completed|from|at)\b", line_clean, re.IGNORECASE)
                if match_same:
                    degree = f"{level} of {match_same.group(3).strip()}"
                    source_deg_line = line
                    break

                # Fallback to simple matching on line
                match_simple = re.search(r"\b((?:Bachelor|Master|Doctor|Diploma)\s+(?:of|in)\s+[A-Za-z\s\-]{3,30})\b", line_clean, re.IGNORECASE)
                if match_simple:
                    degree = match_simple.group(1).strip()
                    source_deg_line = line
                    break

        if degree:
            degree = degree.strip(",. ").title()
            degree = re.sub(r"\bOf\b", "of", degree)
            degree = re.sub(r"\bIn\b", "in", degree)

        # 4. Parse Name Candidate
        candidate_name = None
        source_name_line = None
        for line in text_lines:
            line_clean = line.strip()
            # Match: "<Name> has been admitted to / has completed / was awarded"
            match = re.search(
                r"^([A-Z][A-Z\s\.\-]{2,30}?)\s+(?:has\s+been\s+admitted|admitted\s+to|has\s+completed|was\s+awarded|is\s+hereby|having\s+completed)\b",
                line_clean,
                re.IGNORECASE
            )
            if match:
                candidate_name = match.group(1).strip()
                source_name_line = line
                break

        if not candidate_name:
            for idx, line in enumerate(text_lines):
                line_clean = line.strip()
                if re.search(r"\b(certify that|admitted to|conferred upon|award to)\b", line_clean, re.IGNORECASE):
                    match_same = re.search(r"\b(?:certify\s+that|admitted\s+to|conferred\s+upon|award\s+to)\s+([A-Z][A-Za-z\s\.\-]{2,30}?)\b", line_clean, re.IGNORECASE)
                    if match_same:
                        candidate_name = match_same.group(1).strip()
                        source_name_line = line
                        break
                    if idx + 1 < len(text_lines):
                        next_line = text_lines[idx + 1].strip()
                        if len(next_line) < 40 and not re.search(r"\b(and|the|having|has|completed|degree|faculty|engineering|science|university|college|office|dated|held)\b", next_line, re.IGNORECASE):
                            candidate_name = next_line
                            source_name_line = text_lines[idx + 1]
                            break

        if candidate_name:
            candidate_name = candidate_name.strip(",. ")

        # 5. Confidence score calculation based on OCR line confidence values
        field_scores = []
        for field_val, source_line in [(university, source_uni_line), (degree, source_deg_line), (candidate_name, source_name_line), (year, source_year_line)]:
            if field_val is None:
                field_scores.append(0.0)
            else:
                score = 0.9
                if source_line:
                    matched_scores = []
                    for k, s in self.line_confidences.items():
                        if k.lower() in source_line.lower() or source_line.lower() in k.lower():
                            matched_scores.append(s)
                    if matched_scores:
                        score = sum(matched_scores) / len(matched_scores)
                elif university:  # university fallback matching
                    for k, s in self.line_confidences.items():
                        if university.lower() in k.lower() or k.lower() in university.lower():
                            score = s
                            break
                field_scores.append(score)

        confidence_score = sum(field_scores) / 4.0
        confidence_level = "HIGH" if confidence_score >= 0.75 else "MEDIUM" if confidence_score >= 0.5 else "LOW"

        return {
            "university": university,
            "degree": degree,
            "name": candidate_name,
            "graduation_year": year,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level
        }

    def get_mock_metadata(self, filename: str) -> Dict[str, Any]:
        """
        Mock helper that maps specific filenames to test mock outputs.
        """
        lower_name = filename.lower()
        if "mit" in lower_name:
            return {
                "university": "Massachusetts Institute of Technology",
                "degree": "Bachelor of Science in Physics",
                "name": "Tutor User",
                "graduation_year": 2019,
                "confidence_score": 1.0,
                "confidence_level": "HIGH"
            }
        elif "stanford" in lower_name:
            return {
                "university": "Stanford University",
                "degree": "Master of Computer Science",
                "name": "Tutor",  # Partial mismatch (~66% similarity) to "Tutor User"
                "graduation_year": 2021,
                "confidence_score": 0.8,
                "confidence_level": "HIGH"
            }
        elif "mismatch" in lower_name:
            return {
                "university": "Harvard University",
                "degree": "Doctor of Art History",
                "name": "Completely Different Name",
                "graduation_year": 1995,
                "confidence_score": 0.9,
                "confidence_level": "HIGH"
            }
        elif "low_confidence" in lower_name:
            return {
                "university": None,
                "degree": "B.Sc",
                "name": None,
                "graduation_year": None,
                "confidence_score": 0.25,
                "confidence_level": "LOW"
            }
        
        # Default mock fallback
        return {
            "university": "State University",
            "degree": "Bachelor of Education",
            "name": "Tutor User",
            "graduation_year": 2018,
            "confidence_score": 0.75,
            "confidence_level": "MEDIUM"
        }
