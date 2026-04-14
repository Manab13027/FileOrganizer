"""
Advanced date detection engine with priority logic
"""
import re
from datetime import datetime
from pathlib import Path

class DateDetector:
    """Detect dates from multiple sources with priority logic"""
    
    def __init__(self):
        # Comprehensive date patterns
        self.patterns = {
            # ISO formats
            'iso_date': [
                (r'(\d{4})-(\d{2})-(\d{2})', 'YYYY-MM-DD'),
                (r'(\d{4})_(\d{2})_(\d{2})', 'YYYY_MM_DD'),
                (r'(\d{4})\.(\d{2})\.(\d{2})', 'YYYY.MM.DD'),
            ],
            # European formats
            'eu_date': [
                (r'(\d{2})-(\d{2})-(\d{4})', 'DD-MM-YYYY'),
                (r'(\d{2})_(\d{2})_(\d{4})', 'DD_MM_YYYY'),
                (r'(\d{2})\.(\d{2})\.(\d{4})', 'DD.MM.YYYY'),
            ],
            # US formats
            'us_date': [
                (r'(\d{2})-(\d{2})-(\d{4})', 'MM-DD-YYYY'),
                (r'(\d{2})_(\d{2})_(\d{4})', 'MM_DD_YYYY'),
                (r'(\d{2})\.(\d{2})\.(\d{4})', 'MM.DD.YYYY'),
            ],
            # Compact formats
            'compact': [
                (r'(\d{4})(\d{2})(\d{2})', 'YYYYMMDD'),
                (r'(\d{2})(\d{2})(\d{4})', 'MMDDYYYY'),
            ],
            # Year-month formats
            'year_month': [
                (r'(\d{4})-(\d{2})', 'YYYY-MM'),
                (r'(\d{4})_(\d{2})', 'YYYY_MM'),
                (r'(\d{4})(\d{2})', 'YYYYMM'),
            ],
            # Month-year formats
            'month_year': [
                (r'(\d{2})-(\d{4})', 'MM-YYYY'),
                (r'(\d{2})_(\d{4})', 'MM_YYYY'),
                (r'(\d{2})(\d{4})', 'MMYYYY'),
            ],
            # Text formats
            'text_date': [
                (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,_-]+(\d{1,2})[\s,_-]+(\d{4})', 
                 'Month DD, YYYY'),
                (r'(\d{1,2})[\s,_-]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,_-]+(\d{4})',
                 'DD Month YYYY'),
                (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,_-]+(\d{4})',
                 'Month YYYY'),
                (r'(\d{4})[\s,_-]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*',
                 'YYYY Month'),
            ]
        }
        
        # Month name mappings
        self.month_names = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        
        # Priority weights (higher = more important)
        self.priority_weights = {
            'iso_date': 100,
            'compact': 95,
            'year_month': 90,
            'eu_date': 85,
            'us_date': 85,
            'month_year': 80,
            'text_date': 75
        }
    
    def detect_from_filename(self, filename):
        """Detect all possible dates from filename"""
        results = []
        stem = Path(filename).stem.lower()
        
        # Check each pattern category
        for category, pattern_list in self.patterns.items():
            for pattern, pattern_name in pattern_list:
                matches = re.finditer(pattern, stem, re.IGNORECASE)
                for match in matches:
                    try:
                        year, month = self._parse_match(match, category)
                        if year and month:
                            # Calculate confidence
                            confidence = self.priority_weights.get(category, 50)
                            
                            # Penalize if year is unreasonable
                            if year < 1900 or year > 2100:
                                confidence -= 20
                            
                            results.append({
                                'year': year,
                                'month': month,
                                'confidence': confidence,
                                'category': category,
                                'pattern': pattern_name,
                                'source': 'filename',
                                'match': match.group()
                            })
                    except (ValueError, IndexError):
                        continue
        
        # Sort by confidence (highest first)
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results
    
    def _parse_match(self, match, category):
        """Parse regex match into year and month"""
        groups = match.groups()
        
        try:
            if category == 'iso_date':
                return int(groups[0]), int(groups[1])
            
            elif category == 'eu_date':
                return int(groups[2]), int(groups[1])
            
            elif category == 'us_date':
                return int(groups[2]), int(groups[0])
            
            elif category == 'compact':
                if len(groups[0]) == 4:  # YYYYMMDD
                    return int(groups[0]), int(groups[1])
                else:  # MMDDYYYY
                    return int(groups[2]), int(groups[0])
            
            elif category == 'year_month':
                return int(groups[0]), int(groups[1])
            
            elif category == 'month_year':
                return int(groups[1]), int(groups[0])
            
            elif category == 'text_date':
                if len(groups) == 3:
                    # Month DD, YYYY or DD Month YYYY
                    if groups[0].isalpha():  # Month DD, YYYY
                        month_str = groups[0].lower()
                        year = int(groups[2])
                    else:  # DD Month YYYY
                        month_str = groups[1].lower()
                        year = int(groups[2])
                else:  # Month YYYY or YYYY Month
                    if groups[0].isalpha():  # Month YYYY
                        month_str = groups[0].lower()
                        year = int(groups[1])
                    else:  # YYYY Month
                        month_str = groups[1].lower()
                        year = int(groups[0])
                
                month = self.month_names.get(month_str[:3])
                return year, month
        
        except (ValueError, IndexError, KeyError):
            return None, None
    
    def get_best_filename_date(self, filename):
        """Get the best date from filename"""
        dates = self.detect_from_filename(filename)
        return dates[0] if dates else None

# Example usage
if __name__ == "__main__":
    detector = DateDetector()
    
    test_files = [
        "vacation_2023-07-15.jpg",
        "report_15-07-2023.pdf",
        "photo_20230715.png",
        "invoice_07-2023.docx",
        "project_July_2023.zip",
        "meeting_2023_07_15.mp4"
    ]
    
    for filename in test_files:
        result = detector.get_best_filename_date(filename)
        if result:
            print(f"{filename}: {result['year']}-{result['month']:02d} (confidence: {result['confidence']})")
        else:
            print(f"{filename}: No date found")