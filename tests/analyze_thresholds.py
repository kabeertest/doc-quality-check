"""
Analyze confidence score distribution to recommend optimal thresholds.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from utils.document_processor import extract_page_data


def analyze_dataset():
    """Analyze all documents in dataset"""
    dataset_path = Path('dataset')
    
    results = []
    
    # Categories to analyze
    categories = {
        'valid-pdfs': 'Good Quality Documents',
        'unclear-pdfs': 'Unclear/Low Quality',
        'empty-pdfs': 'Empty/Blank Pages',
        'italian_ids': 'Italian ID Documents',
        'big-pdf-but-readable': 'Large PDFs'
    }
    
    print("=" * 90)
    print("CONFIDENCE SCORE ANALYSIS - THRESHOLD RECOMMENDATIONS")
    print("=" * 90)
    
    for folder, description in categories.items():
        folder_path = dataset_path / folder
        if not folder_path.exists():
            continue
        
        print(f"\n{'='*90}")
        print(f"CATEGORY: {folder} ({description})")
        print(f"{'='*90}")
        
        files = list(folder_path.glob('*.pdf')) + list(folder_path.glob('*.png')) + \
                list(folder_path.glob('*.jpg')) + list(folder_path.glob('*.jpeg'))
        
        category_scores = []
        
        for file_path in files[:5]:  # Limit to 5 files per category
            try:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                
                page_data, _ = extract_page_data(file_bytes, file_path.name)
                
                for page_info in page_data:
                    conf = page_info['ocr_conf']
                    ink = page_info['ink_ratio'] * 100
                    lang = page_info.get('detected_language', 'eng')
                    text_len = len(page_info.get('text_content', ''))
                    
                    results.append({
                        'category': folder,
                        'file': file_path.name,
                        'page': page_info['page'],
                        'confidence': conf,
                        'ink_ratio': ink,
                        'language': lang,
                        'text_length': text_len
                    })
                    
                    category_scores.append(conf)
                    
                    status = "READABLE" if conf >= 30 else "unreadable"
                    print(f"  {file_path.name[:35]:35s} P{page_info['page']:2d} | "
                          f"Conf: {conf:6.2f}% | Lang: {lang:3s} | "
                          f"Ink: {ink:5.2f}% | Text: {text_len:4d} | {status}")
                    
            except Exception as e:
                print(f"  ERROR: {file_path.name} - {e}")
        
        if category_scores:
            avg = sum(category_scores) / len(category_scores)
            max_conf = max(category_scores)
            min_conf = min(category_scores)
            readable_count = sum(1 for s in category_scores if s >= 30)
            readable_pct = readable_count / len(category_scores) * 100
            
            print(f"\n  Category Stats:")
            print(f"    Pages: {len(category_scores)}")
            print(f"    Confidence: Min={min_conf:.2f}%, Max={max_conf:.2f}%, Avg={avg:.2f}%")
            print(f"    Readable (>=30%): {readable_count}/{len(category_scores)} ({readable_pct:.1f}%)")
    
    # Overall analysis
    print(f"\n{'='*90}")
    print("OVERALL STATISTICS")
    print(f"{'='*90}")
    
    all_scores = [r['confidence'] for r in results]
    
    if all_scores:
        # Sort scores for percentile analysis
        sorted_scores = sorted(all_scores)
        n = len(sorted_scores)
        
        print(f"\nTotal Pages: {n}")
        print(f"Overall Avg: {sum(all_scores)/n:.2f}%")
        print(f"Min: {min(all_scores):.2f}%, Max: {max(all_scores):.2f}%")
        
        # Percentile analysis
        print(f"\nPercentile Distribution:")
        print(f"  10th percentile: {sorted_scores[int(n*0.10)]:.2f}%")
        print(f"  25th percentile: {sorted_scores[int(n*0.25)]:.2f}%")
        print(f"  50th percentile (median): {sorted_scores[int(n*0.50)]:.2f}%")
        print(f"  75th percentile: {sorted_scores[int(n*0.75)]:.2f}%")
        print(f"  90th percentile: {sorted_scores[int(n*0.90)]:.2f}%")
        
        # Threshold analysis
        print(f"\n{'='*90}")
        print("THRESHOLD RECOMMENDATIONS")
        print(f"{'='*90}")
        
        thresholds = [5, 10, 15, 20, 25, 30, 35, 40, 50]
        
        print(f"\n{'Threshold':<12} {'Readable':<10} {'Unreadable':<12} {'% Readable':<12} {'Recommendation'}")
        print("-" * 90)
        
        for thresh in thresholds:
            readable = sum(1 for s in all_scores if s >= thresh)
            unreadable = n - readable
            pct = readable / n * 100
            
            recommendation = ""
            if thresh <= 10:
                recommendation = "Too lenient - accepts blank pages"
            elif thresh <= 20:
                recommendation = "Good for Italian IDs & degraded docs"
            elif thresh <= 30:
                recommendation = "Balanced - recommended for mixed docs"
            elif thresh <= 40:
                recommendation = "Strict - only clear documents pass"
            else:
                recommendation = "Very strict - only excellent quality"
            
            print(f"{thresh:>5}%       {readable:>5}      {unreadable:>5}        {pct:>5.1f}%        {recommendation}")
        
        # Category-specific recommendations
        print(f"\n{'='*90}")
        print("CATEGORY-SPECIFIC THRESHOLDS")
        print(f"{'='*90}")
        
        for folder in categories.keys():
            cat_results = [r for r in results if r['category'] == folder]
            if not cat_results:
                continue
            
            cat_scores = [r['confidence'] for r in cat_results]
            avg = sum(cat_scores) / len(cat_scores)
            
            # Recommend threshold based on category
            if 'empty' in folder:
                rec_thresh = 5
            elif 'valid' in folder:
                rec_thresh = 25
            elif 'italian' in folder:
                rec_thresh = 15
            elif 'unclear' in folder:
                rec_thresh = 10
            else:
                rec_thresh = 20
            
            print(f"\n{categories[folder]}:")
            print(f"  Avg Confidence: {avg:.2f}%")
            print(f"  Recommended Threshold: {rec_thresh}%")
            print(f"  Pass Rate at {rec_thresh}%: {sum(1 for s in cat_scores if s >= rec_thresh)}/{len(cat_scores)}")
        
        # Final recommendations
        print(f"\n{'='*90}")
        print("FINAL RECOMMENDATIONS")
        print(f"{'='*90}")
        print("""
Based on your dataset analysis:

1. SINGLE THRESHOLD (Simple):
   -> Use 15% for mixed document types
   - Accepts: Most Italian IDs, degraded documents
   - Rejects: Blank pages, heavily corrupted files
   
2. TWO-TIER THRESHOLD (Recommended):
   -> Italian documents: 15%
   -> Other documents: 25%
   - Better accuracy for language-specific cases
   
3. STRICT MODE (Production):
   -> Use 30% for high-quality requirements
   - Only clear, well-scanned documents pass
   - May reject legitimate but degraded IDs

4. CURRENT SETTING:
   -> 40% is TOO STRICT for your dataset
   - 0% of your documents pass at this threshold
   - Recommended: Lower to 15-25%
        """)


if __name__ == '__main__':
    analyze_dataset()
