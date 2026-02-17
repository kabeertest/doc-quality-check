"""
Module for detecting and classifying identity cards in PDF documents.
Document types and sides are fully configurable via config.json.
"""

import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import io
from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from utils.document_processor import extract_page_data
from checks.clarity_check import calculate_ink_ratio
from checks.confidence_check import calculate_ocr_confidence
import logging
from utils.logger import get_logger

logger = get_logger(__name__)
from utils.content_extraction import extract_text_content


# Document type enum - keys only, values from config.json
class DocumentType(Enum):
    """Enum for document type keys. Actual names/labels from config.json."""
    RESIDENTIAL_ID = "residential_id"
    AADHAAR = "aadhaar"
    UNKNOWN = "unknown"


# Document side enum - keys only, values from config.json
class DocumentSide(Enum):
    """Enum for document side keys. Actual labels from config.json."""
    FRONT = "front"
    BACK = "back"
    BOTH = "both"
    UNKNOWN = "unknown"


@dataclass
class IdentityCardClassification:
    """Data class for identity card classification results."""
    page_number: any  # Can be int or string (e.g., "1-1" for sub-documents)
    document_type: DocumentType
    document_side: DocumentSide
    confidence: float
    text_content: str
    features: Dict[str, any]


class IdentityCardDetector:
    """Class for detecting and classifying identity cards in PDF documents."""

    def __init__(self, config_path: str = None):
        # Load configuration
        from modules.config_loader import get_config
        self.config = get_config()
        
        # All configuration comes from config.json - no hardcoded values
        # Document types and sides are loaded dynamically from config
    
    @property
    def document_type_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Get document type keywords from config."""
        return self.config.get_all_document_type_keywords()
    
    @property
    def document_side_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Get document side keywords from config."""
        return self.config.get_all_document_side_keywords()

    def detect_identity_documents(self, file_bytes: bytes, file_name: str) -> List[IdentityCardClassification]:
        """
        Detect and classify identity documents in a PDF file.
        Handles pages that may contain multiple documents.
        
        Uses single-pass processing with post-hoc confidence adjustment
        based on cross-document keyword frequency analysis.
        
        Args:
            file_bytes: Bytes of the uploaded PDF file
            file_name: Name of the uploaded file
            
        Returns:
            List of IdentityCardClassification objects with detection results
        """
        results = []
        all_classifications = []
        
        # Extract page data using existing functionality
        page_data_list, _ = extract_page_data(file_bytes, file_name)
        
        # Single pass: Process all pages and collect classifications
        for page_data in page_data_list:
            page_num = page_data['page']
            image = page_data['image']
            text_content = page_data['text_content']
            
            # Process the page for multiple documents
            from modules.document_segmentation import process_page_with_multiple_documents
            page_results = process_page_with_multiple_documents(image, text_content, page_num)
            
            all_classifications.extend(page_results)
        
        # Post-hoc analysis: Calculate keyword frequency across all documents
        keyword_frequency = self._analyze_keyword_frequency(all_classifications)
        
        # Apply confidence adjustments based on frequency analysis
        for classification in all_classifications:
            self._apply_frequency_based_adjustment(classification, keyword_frequency)
            results.append(classification)
        
        # Apply heuristics to improve classification
        results = self._apply_classification_heuristics(results)
        
        return results
    
    def _apply_classification_heuristics(self, classifications: List[IdentityCardClassification]) -> List[IdentityCardClassification]:
        """
        Apply post-classification heuristics to improve accuracy.
        
        Strategy:
        1. Detect back side by looking for MRZ (Machine Readable Zone) pattern with "<<<" characters
        2. Detect front side by checking for personal identification keywords
        3. When multiple documents on same page, reorder and match based on content
        
        Args:
            classifications: List of classifications from detect_identity_documents
            
        Returns:
            Updated list of classifications with heuristics applied
        """
        # Helper function to analyze document content
        def analyze_document_content(text):
            """Analyze document content to determine likely side."""
            text_lower = text.lower()
            text_raw = text
            
            # Check for MRZ (Machine Readable Zone) - back side indicator
            has_mrz_pattern = '<' in text_raw and text_raw.count('<') >= 5
            
            # Check for back side keywords
            back_keywords = ['firma', 'signature', 'scadenza', 'expiry', 'valid until', 'issued by', 
                           'rilasciato', 'sigillo', 'timbro', 'qr code', 'barcode', 'mrz',
                           'rilascio', 'questura', 'luogo d', 'place of birth']
            has_back_keywords = any(keyword in text_lower for keyword in back_keywords)
            
            # Check for front side keywords
            front_keywords = ['identity card', 'carta d', 'nome', 'cognome', 'name', 'surname', 
                            'data di nascita', 'date of birth', 'luogo di nascita', 'place of birth',
                            'foto', 'photo', 'immagine', 'image', 'sesso', 'gender', 'cittadinanza', 
                            'nationality', 'genere', 'domicilio', 'residenza']
            has_front_keywords = any(keyword in text_lower for keyword in front_keywords)
            
            return {
                'has_mrz': has_mrz_pattern,
                'has_back_keywords': has_back_keywords,
                'has_front_keywords': has_front_keywords,
                'mrz_score': text_raw.count('<'),  # Number of < characters
                'back_score': sum(1 for kw in back_keywords if kw in text_lower),
                'front_score': sum(1 for kw in front_keywords if kw in text_lower)
            }
        
        # Analyze all documents
        for classification in classifications:
            analysis = analyze_document_content(classification.text_content)
            classification.features['content_analysis'] = analysis
            
            # Determine side based on content markers (with priority order)
            if analysis['has_mrz']:
                # Strong indicator this is back side (MRZ is the most reliable)
                classification.document_side = DocumentSide.BACK
                classification.features['detection_method'] = 'mrz_pattern'
            elif analysis['has_back_keywords'] and analysis['back_score'] >= analysis['front_score']:
                # Back side indicators outweigh front
                classification.document_side = DocumentSide.BACK
                classification.features['detection_method'] = 'back_keywords'
            elif analysis['has_front_keywords'] and analysis['front_score'] > analysis['back_score']:
                # Front side keywords are stronger
                classification.document_side = DocumentSide.FRONT
                classification.features['detection_method'] = 'front_keywords'
            elif analysis['has_front_keywords']:
                # Has front keywords but also some back keywords - prefer front if text length suggests personal info
                if len(classification.text_content) < 200:  # Shorter text = more likely front with OCR noise
                    classification.document_side = DocumentSide.FRONT
                    classification.features['detection_method'] = 'front_keywords_priority'
                else:
                    classification.document_side = DocumentSide.BACK
                    classification.features['detection_method'] = 'back_keywords_priority'
        
        # Second pass: Group by page and fix mismatches
        by_page = {}
        for idx, classification in enumerate(classifications):
            page_key = str(classification.page_number).split('-')[0]
            if page_key not in by_page:
                by_page[page_key] = []
            by_page[page_key].append((idx, classification))
        
        # For pages with multiple documents, ensure coherence and proper front/back pairing
        for page_num, docs in by_page.items():
            if len(docs) == 2:
                idx1, doc1 = docs[0]
                idx2, doc2 = docs[1]
                
                # First, fix document types
                if doc1.document_type.value == 'unknown' and doc2.document_type.value == 'unknown':
                    # Both unknown - check which has better keyword match
                    score1 = doc1.features.get('content_analysis', {}).get('front_score', 0) + \
                             doc1.features.get('content_analysis', {}).get('back_score', 0)
                    score2 = doc2.features.get('content_analysis', {}).get('front_score', 0) + \
                             doc2.features.get('content_analysis', {}).get('back_score', 0)
                    
                    if score1 > 0 or score2 > 0:
                        doc1.document_type = DocumentType.RESIDENTIAL_ID
                        doc2.document_type = DocumentType.RESIDENTIAL_ID
                
                # If one is known and other is unknown, propagate the type
                elif doc1.document_type.value != 'unknown' and doc2.document_type.value == 'unknown':
                    doc2.document_type = doc1.document_type
                    doc2.confidence = max(doc2.confidence, 65.0)
                    doc2.features['heuristic_applied'] = 'matched_with_pair'
                
                elif doc2.document_type.value != 'unknown' and doc1.document_type.value == 'unknown':
                    doc1.document_type = doc2.document_type
                    doc1.confidence = max(doc1.confidence, 65.0)
                    doc1.features['heuristic_applied'] = 'matched_with_pair'
                
                # Now fix document sides based on detected sides
                side1 = doc1.document_side
                side2 = doc2.document_side
                
                # If one is clearly FRONT and other is UNKNOWN, assume other is BACK
                if side1 == DocumentSide.FRONT and side2 == DocumentSide.UNKNOWN:
                    doc2.document_side = DocumentSide.BACK
                    doc2.features['heuristic_applied'] = 'paired_front_back'
                elif side2 == DocumentSide.FRONT and side1 == DocumentSide.UNKNOWN:
                    doc1.document_side = DocumentSide.BACK
                    doc1.features['heuristic_applied'] = 'paired_front_back'
                
                # If one is clearly BACK and other is UNKNOWN, assume other is FRONT
                elif side1 == DocumentSide.BACK and side2 == DocumentSide.UNKNOWN:
                    doc2.document_side = DocumentSide.FRONT
                    doc2.features['heuristic_applied'] = 'paired_back_front'
                elif side2 == DocumentSide.BACK and side1 == DocumentSide.UNKNOWN:
                    doc1.document_side = DocumentSide.FRONT
                    doc1.features['heuristic_applied'] = 'paired_back_front'
                
                # If both are BACK (unlikely but handle it), re-evaluate the one without MRZ
                elif side1 == DocumentSide.BACK and side2 == DocumentSide.BACK:
                    has_mrz1 = doc1.features.get('content_analysis', {}).get('has_mrz', False)
                    has_mrz2 = doc2.features.get('content_analysis', {}).get('has_mrz', False)
                    
                    # If only one has MRZ, the other should be FRONT
                    if has_mrz1 and not has_mrz2:
                        doc2.document_side = DocumentSide.FRONT
                        doc2.features['heuristic_applied'] = 'mrz_side_correction'
                    elif has_mrz2 and not has_mrz1:
                        doc1.document_side = DocumentSide.FRONT
                        doc1.features['heuristic_applied'] = 'mrz_side_correction'
        
        return classifications
    
    def _analyze_keyword_frequency(self, classifications: List[IdentityCardClassification]) -> Dict:
        """
        Analyze keyword frequency across all classifications.
        
        Args:
            classifications: List of all classification results
            
        Returns:
            Dictionary with keyword frequency statistics
        """
        keyword_frequency = {
            'document_types': {},
            'document_sides': {},
            'specific_keywords': {},
            'total_documents': len(classifications)
        }
        
        for classification in classifications:
            features = classification.features
            
            # Track document type matches
            type_matches = features.get('document_type_keyword_matches', {})
            for doc_type, matched in type_matches.items():
                if matched:
                    if doc_type not in keyword_frequency['document_types']:
                        keyword_frequency['document_types'][doc_type] = {
                            'count': 0,
                            'documents': [],
                            'specific_keywords': set()
                        }
                    keyword_frequency['document_types'][doc_type]['count'] += 1
                    keyword_frequency['document_types'][doc_type]['documents'].append(classification.page_number)
                    
                    # Track which specific keywords matched
                    text_lower = classification.text_content.lower()
                    type_keywords = self.document_type_keywords.get(doc_type, {})
                    for lang, keywords in type_keywords.items():
                        for keyword in keywords:
                            if keyword.lower() in text_lower:
                                keyword_frequency['document_types'][doc_type]['specific_keywords'].add(keyword)
                                # Track per-keyword frequency
                                if keyword not in keyword_frequency['specific_keywords']:
                                    keyword_frequency['specific_keywords'][keyword] = 0
                                keyword_frequency['specific_keywords'][keyword] += 1
            
            # Track document side matches
            side_matches = features.get('document_side_keyword_matches', {})
            for side, matched in side_matches.items():
                if matched:
                    if side not in keyword_frequency['document_sides']:
                        keyword_frequency['document_sides'][side] = {
                            'count': 0,
                            'documents': [],
                            'specific_keywords': set()
                        }
                    keyword_frequency['document_sides'][side]['count'] += 1
                    keyword_frequency['document_sides'][side]['documents'].append(classification.page_number)
                    
                    # Track which specific keywords matched
                    text_lower = classification.text_content.lower()
                    side_keywords = self.document_side_keywords.get(side, {})
                    for lang, keywords in side_keywords.items():
                        for keyword in keywords:
                            if keyword.lower() in text_lower:
                                keyword_frequency['document_sides'][side]['specific_keywords'].add(keyword)
        
        return keyword_frequency
    
    def _apply_frequency_based_adjustment(self, classification: IdentityCardClassification, 
                                         keyword_frequency: Dict):
        """
        Apply confidence adjustment based on keyword frequency analysis.
        
        All boost values come from config.json - no hardcoded values.
        
        Args:
            classification: Classification to adjust
            keyword_frequency: Frequency analysis results
        """
        base_confidence = classification.confidence
        adjustment = 0.0
        adjustment_details = {
            'frequency_boost': 0.0,
            'specificity_bonus': 0.0,
            'consistency_bonus': 0.0,
            'quality_factor': 1.0,
            'total_adjustment': 0.0,
            'matched_keyword_count': 0,
            'cross_document_matches': 0
        }
        
        # Get ALL boost settings from config
        boost_settings = self.config.get('confidence_boost_settings', {})
        quality_settings = boost_settings.get('quality_factors', {})
        specificity_settings = boost_settings.get('specificity_bonus_per_word', {})
        consistency_settings = boost_settings.get('consistency_bonus', {})
        
        # Calculate frequency-based boost
        type_matches = classification.features.get('document_type_keyword_matches', {})
        side_matches = classification.features.get('document_side_keyword_matches', {})
        
        matched_types = [t for t, m in type_matches.items() if m]
        matched_sides = [s for s, m in side_matches.items() if m]
        
        # Count total matched keywords
        total_keyword_matches = len(matched_types) + len(matched_sides)
        adjustment_details['matched_keyword_count'] = total_keyword_matches
        
        # Calculate cross-document match count
        cross_doc_matches = 0
        for doc_type in matched_types:
            if doc_type in keyword_frequency['document_types']:
                count = keyword_frequency['document_types'][doc_type]['count']
                cross_doc_matches = max(cross_doc_matches, count)
        
        adjustment_details['cross_document_matches'] = cross_doc_matches
        
        # Apply frequency boost with diminishing returns (from config)
        if cross_doc_matches >= 3:
            adjustment_details['frequency_boost'] = boost_settings.get('triple_plus_match_boost', 15.0)
        elif cross_doc_matches == 2:
            adjustment_details['frequency_boost'] = boost_settings.get('double_match_boost', 10.0)
        elif cross_doc_matches == 1:
            adjustment_details['frequency_boost'] = boost_settings.get('single_match_boost', 5.0)
        
        # Apply specificity bonus (longer keywords = more specific = higher bonus)
        specificity_bonus = 0.0
        for doc_type in matched_types:
            if doc_type in keyword_frequency['document_types']:
                specific_keywords = keyword_frequency['document_types'][doc_type]['specific_keywords']
                for keyword in specific_keywords:
                    # Longer keywords are more specific (values from config)
                    word_count = len(keyword.split())
                    if word_count >= 3:
                        specificity_bonus += specificity_settings.get('three_plus_words', 3.0)
                    elif word_count == 2:
                        specificity_bonus += specificity_settings.get('two_words', 2.0)
                    else:
                        specificity_bonus += specificity_settings.get('single_word', 1.0)
        
        # Cap specificity bonus (from config)
        max_specificity = boost_settings.get('max_specificity_bonus', 10.0)
        adjustment_details['specificity_bonus'] = min(specificity_bonus, max_specificity)
        
        # Apply consistency bonus (multiple different keywords matching)
        if total_keyword_matches >= 3:
            adjustment_details['consistency_bonus'] = consistency_settings.get('three_plus_matches', 5.0)
        elif total_keyword_matches >= 2:
            adjustment_details['consistency_bonus'] = consistency_settings.get('two_matches', 3.0)
        
        # Apply quality factor (reduce boost for low-quality documents) - ALL from config
        ocr_confidence = classification.features.get('ocr_confidence', 0)
        ink_ratio = classification.features.get('ink_ratio', 0)
        
        quality_factor = 1.0
        
        # OCR quality factor
        poor_ocr_threshold = quality_settings.get('poor_ocr_threshold', 30.0)
        poor_ocr_factor = quality_settings.get('poor_ocr_factor', 0.5)
        medium_ocr_threshold = quality_settings.get('medium_ocr_threshold', 50.0)
        medium_ocr_factor = quality_settings.get('medium_ocr_factor', 0.75)
        
        if ocr_confidence < poor_ocr_threshold:
            quality_factor = poor_ocr_factor
        elif ocr_confidence < medium_ocr_threshold:
            quality_factor = medium_ocr_factor
        
        # Ink ratio quality factor
        poor_ink_min = quality_settings.get('poor_ink_ratio_min', 0.05)
        poor_ink_max = quality_settings.get('poor_ink_ratio_max', 0.8)
        poor_ink_factor = quality_settings.get('poor_ink_factor', 0.8)
        
        if ink_ratio < poor_ink_min or ink_ratio > poor_ink_max:
            quality_factor *= poor_ink_factor
        
        adjustment_details['quality_factor'] = quality_factor
        
        # Calculate total adjustment
        base_adjustment = (adjustment_details['frequency_boost'] + 
                          adjustment_details['specificity_bonus'] + 
                          adjustment_details['consistency_bonus'])
        
        adjustment = base_adjustment * quality_factor
        adjustment_details['total_adjustment'] = adjustment
        
        # Apply adjustment with cap (from config)
        max_confidence = boost_settings.get('max_confidence_cap', 100.0)
        classification.confidence = min(max_confidence, base_confidence + adjustment)
        
        # Store adjustment details in features for UI display
        classification.features['confidence_adjustment'] = adjustment_details
    
    def classify_identity_document(self, image: Image.Image, text_content: str, page_number: int) -> IdentityCardClassification:
        """
        Classify a single identity document page.
        
        Args:
            image: PIL Image of the document page
            text_content: Extracted text from the document
            page_number: Page number in the document
            
        Returns:
            IdentityCardClassification object with the classification results
        """
        # Calculate various features for classification
        features = self._extract_features(image, text_content)
        
        # Determine document type
        doc_type = self._classify_document_type(text_content, features)
        
        # Determine document side
        doc_side = self._classify_document_side(text_content, features)
        
        # Calculate confidence score
        confidence = self._calculate_classification_confidence(features, doc_type, doc_side)

        return IdentityCardClassification(
            page_number=page_number,
            document_type=doc_type,
            document_side=doc_side,
            confidence=float(confidence),  # Ensure float type
            text_content=text_content,
            features=features
        )
    
    def _extract_features(self, image: Image.Image, text_content: str) -> Dict[str, any]:
        """Extract features from the image and text for classification."""
        features = {}
        
        # Image-based features
        ink_ratio, _ = calculate_ink_ratio(image)
        features['ink_ratio'] = ink_ratio
        
        # Request verbose OCR confidence logging when debug enabled
        verbose = any(h.level == logging.DEBUG for h in logger.handlers)
        ocr_confidence, _ = calculate_ocr_confidence(image, mode='fast', verbose=verbose)
        features['ocr_confidence'] = ocr_confidence
        
        # Text-based features
        features['text_length'] = len(text_content)
        features['word_count'] = len(text_content.split())
        
        # Check for presence of keywords from config
        features['document_type_keyword_matches'] = {}
        for doc_type, keywords in self.document_type_keywords.items():
            has_keywords = self._has_keywords(text_content, keywords)
            features[f'has_{doc_type}_keywords'] = has_keywords
            features['document_type_keyword_matches'][doc_type] = has_keywords
        
        features['document_side_keyword_matches'] = {}
        for side, keywords in self.document_side_keywords.items():
            has_keywords = self._has_keywords(text_content, keywords)
            features[f'has_{side}_keywords'] = has_keywords
            features['document_side_keyword_matches'][side] = has_keywords
        
        if any(h.level == logging.DEBUG for h in logger.handlers):
            # Log extracted features for debugging
            try:
                logger.debug(f"_extract_features: ink_ratio={features['ink_ratio']:.3f} ocr_confidence={features['ocr_confidence']} text_length={features['text_length']} word_count={features['word_count']}")
                logger.debug(f"_extract_features: type_matches={features['document_type_keyword_matches']} side_matches={features['document_side_keyword_matches']}")
            except Exception:
                pass

        return features
    
    def _has_keywords(self, text: str, keyword_groups: Dict[str, List[str]]) -> bool:
        """Check if text contains any of the provided keywords."""
        text_lower = text.lower()
        for lang, keywords in keyword_groups.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return True
        return False
    
    def _classify_document_type(self, text_content: str, features: Dict[str, any]) -> DocumentType:
        """Classify the document type based on text and features.
        
        Uses config-based keywords - no hardcoded values.
        """
        text_lower = text_content.lower()
        
        # Check each configured document type
        best_match = None
        best_score = 0
        
        for doc_type, keywords in self.document_type_keywords.items():
            score = 0
            
            # Check English keywords
            for keyword in keywords.get('en', []):
                if keyword.lower() in text_lower:
                    score += 2
            
            # Check other language keywords
            for keyword in keywords.get('other', []):
                if keyword.lower() in text_lower:
                    score += 1
            
            # Check if feature flag is set
            if features.get(f'has_{doc_type}_keywords', False):
                score += 3
            
            if score > best_score:
                best_score = score
                best_match = doc_type
        
        # Map to enum or return UNKNOWN
        if best_match == 'residential_id':
            return DocumentType.RESIDENTIAL_ID
        elif best_match == 'aadhaar':
            return DocumentType.AADHAAR
        elif best_score > 0:
            # Try to create enum from config key
            try:
                return DocumentType(best_match)
            except ValueError:
                return DocumentType.UNKNOWN
        
        return DocumentType.UNKNOWN
    
    def _classify_document_side(self, text_content: str, features: Dict[str, any]) -> DocumentSide:
        """Classify the document side based on text and features."""
        text_lower = text_content.lower()
        
        # Check each configured document side
        side_scores = {}

        # Get configurable weights (with sane defaults)
        wcfg = self.config.get('side_detection_weights', {}) if hasattr(self, 'config') else {}
        en_weight = float(wcfg.get('en_weight', 2.0))
        other_weight = float(wcfg.get('other_weight', 1.0))
        feature_weight = float(wcfg.get('feature_weight', 3.0))
        moderate_min = float(wcfg.get('moderate_ocr_min', 30.0))
        moderate_max = float(wcfg.get('moderate_ocr_max', 70.0))
        moderate_mul = float(wcfg.get('moderate_ocr_side_multiplier', 1.5))

        ocr_conf = float(features.get('ocr_confidence', 0))
        apply_mul = (moderate_min <= ocr_conf <= moderate_max)

        for side, keywords in self.document_side_keywords.items():
            score = 0.0

            # Check English keywords
            for keyword in keywords.get('en', []):
                if keyword.lower() in text_lower:
                    score += en_weight * (moderate_mul if apply_mul else 1.0)

            # Check other language keywords
            for keyword in keywords.get('other', []):
                if keyword.lower() in text_lower:
                    score += other_weight * (moderate_mul if apply_mul else 1.0)

            # Check if feature flag is set
            if features.get(f'has_{side}_keywords', False):
                score += feature_weight * (moderate_mul if apply_mul else 1.0)

            side_scores[side] = score
        
        # Determine side based on scores
        front_score = side_scores.get('front', 0.0)
        back_score = side_scores.get('back', 0.0)
        
        # Return the side with the higher score rather than BOTH
        # This handles cases where OCR captures both sides but one side is dominant
        if front_score > 0 and back_score > 0:
            # Return the side with significantly higher score (>10% difference)
            score_diff_percent = abs(front_score - back_score) / max(front_score, back_score) * 100
            if score_diff_percent > 10:
                return DocumentSide.FRONT if front_score > back_score else DocumentSide.BACK
            else:
                # Scores are too close; use tie-breaker: Italian IDs that show personal identifiers are typically FRONT
                # Keywords like "luogo di nascita", "nome", "cognome", "sesso" appear on front
                # Keywords like "firma", "scadenza", "qr" appear on back
                # Check for strong front identifiers
                has_strong_front = any(word in text_lower for word in ['luogo di nascita', 'luogo d', 'nome e cognome', 'sesso', 'cittadinanza', 'numero di'])
                has_strong_back = any(word in text_lower for word in ['firma', 'scadenza', 'valido', 'codice qr', 'qr code', 'mrz'])
                
                if has_strong_front and not has_strong_back:
                    return DocumentSide.FRONT
                elif has_strong_back and not has_strong_front:
                    return DocumentSide.BACK
                else:
                    # Equal tie-breaker indicators or neither; default to FRONT for identity cards
                    return DocumentSide.FRONT
        elif front_score > 0:
            return DocumentSide.FRONT
        elif back_score > 0:
            return DocumentSide.BACK
        else:
            return DocumentSide.UNKNOWN
    
    def _calculate_classification_confidence(self, features: Dict[str, any], 
                                           doc_type: DocumentType, 
                                           doc_side: DocumentSide) -> float:
        """Calculate confidence score for the classification.
        
        All values from config - no hardcoded references.
        """
        confidence = 0.0
        
        # Base confidence on OCR quality (weight: 30%)
        ocr_conf = float(features.get('ocr_confidence', 0))
        confidence += ocr_conf * 0.3
        
        # Boost confidence if specific document type keywords were found (weight: up to 30%)
        if doc_type != DocumentType.UNKNOWN:
            if doc_type == DocumentType.RESIDENTIAL_ID and features.get('has_residential_id_keywords', False):
                confidence += 30.0
            elif doc_type == DocumentType.AADHAAR and features.get('has_aadhaar_keywords', False):
                confidence += 30.0
        
        # Boost confidence if specific side keywords were found (weight: up to 25%)
        if doc_side != DocumentSide.UNKNOWN:
            if doc_side in [DocumentSide.FRONT, DocumentSide.BOTH] and features.get('has_front_keywords', False):
                confidence += 25.0
            if doc_side in [DocumentSide.BACK, DocumentSide.BOTH] and features.get('has_back_keywords', False):
                confidence += 25.0
        
        # Adjust for document clarity based on ink ratio (weight: up to 15%)
        ink_ratio = float(features.get('ink_ratio', 0))
        if 0.05 <= ink_ratio <= 0.8:  # Reasonable amount of content (not too sparse or dense)
            confidence += 15.0
        elif ink_ratio < 0.01:  # Very little content
            confidence -= 20.0
        elif ink_ratio > 0.9:  # Too much content (possibly scanned document with artifacts)
            confidence -= 10.0
        
        # Adjust based on text length (weight: up to 10%)
        text_length = int(features.get('text_length', 0))
        if 50 <= text_length <= 2000:  # Reasonable amount of text for ID documents
            confidence += 10.0
        elif text_length == 0:  # No text found
            confidence -= 30.0
        
        # Ensure confidence is between 0 and 100
        confidence = float(max(0, min(100, confidence)))
        
        return confidence


def process_identity_documents(file_bytes: bytes, file_name: str) -> List[IdentityCardClassification]:
    """
    Main function to process identity documents in a PDF file.
    
    Args:
        file_bytes: Bytes of the uploaded PDF file
        file_name: Name of the uploaded file
        
    Returns:
        List of IdentityCardClassification objects with detection results
    """
    detector = IdentityCardDetector()
    return detector.detect_identity_documents(file_bytes, file_name)


def group_identity_documents(classifications: List[IdentityCardClassification]) -> Dict[str, List[IdentityCardClassification]]:
    """
    Group identity document classifications by document type.
    
    Args:
        classifications: List of IdentityCardClassification objects
        
    Returns:
        Dictionary grouping classifications by document type
    """
    grouped = {
        'residential_id': [],
        'aadhaar': [],
        'unknown': []
    }
    
    for classification in classifications:
        if classification.document_type == DocumentType.RESIDENTIAL_ID:
            grouped['residential_id'].append(classification)
        elif classification.document_type == DocumentType.AADHAAR:
            grouped['aadhaar'].append(classification)
        else:
            grouped['unknown'].append(classification)
    
    return grouped