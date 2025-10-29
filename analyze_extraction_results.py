import csv
import pandas as pd

# Expected results (ground truth)
EXPECTED_RESULTS = {
    "L01-H01D01-FOS-00-XX-MUP-AR-80050[T0].pdf": {
        "drawing_title": "Mockup External Wall Systems Typical Façade Section Details MEP Door Details",
        "drawing_number": "L01-H01D01-FOS-00-XX-MUP-AR-80050",
        "revision": "T0",
        "latest_revision": "T0",
        "latest_date": "13/10/2023",
        "latest_reason": "Issued for Tender",
        "table_title": "Construction Procurement"
    },
    "L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf": {
        "drawing_title": "Mock-up Room GRMS Layout",
        "drawing_number": "L01-H01D02-WSP-75-XX-MUP-IC-80301",
        "revision": "T1",
        "latest_revision": "T1",
        "latest_date": "07/11/2024",
        "latest_reason": "Issued for Tender",
        "table_title": "Construction Procurement"
    },
    "L02-R02DXX-RSG-00-ZZ-SKT-LS-12801[N0] - Sample Sketch.pdf": {
        "drawing_title": "Pool Enlargement Plan",
        "drawing_number": "L02-R02DXX-RSG-00-ZZ-SKT-LS-12801",
        "revision": "N0",
        "latest_revision": "N0",
        "latest_date": "31/07/25",
        "latest_reason": "Issued for Construction",
        "table_title": "Construction Procurement"
    },
    "L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435[N0] - Sample Sketch.pdf": {
        "drawing_title": "Grading and Drainage Plan 19/34",
        "drawing_number": "L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435",
        "revision": "N0",
        "latest_revision": "N0",
        "latest_date": "31/07/25",
        "latest_reason": "Issued for Construction",
        "table_title": "Construction Procurement"
    },
    "L04-A04D02-CHP-16-00-DWG-SP-10001[N0].pdf": {
        "drawing_title": "Main Pool Piping & Conduit Overall Layout",
        "drawing_number": "L04-A04D02-CHP-16-00-DWG-SP-10001",
        "revision": "N0",
        "latest_revision": "N0",
        "latest_date": "13/08/25",
        "latest_reason": "Issued for Construction",
        "table_title": "Construction Procurement"
    }
}

def analyze_extraction_results():
    """Analyze the extraction results against expected values"""
    
    print("📊 COMPREHENSIVE EXTRACTION ANALYSIS")
    print("=" * 80)
    
    # Read the CSV results
    try:
        with open('pdf_extraction_results_production_final.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            results = list(reader)
    except FileNotFoundError:
        print("❌ Results file not found!")
        return
    
    # Analysis metrics
    total_files = len(results)
    total_fields = 0
    correct_fields = 0
    
    field_accuracy = {
        'drawing_title': {'correct': 0, 'total': 0},
        'drawing_number': {'correct': 0, 'total': 0},
        'revision': {'correct': 0, 'total': 0},
        'latest_revision': {'correct': 0, 'total': 0},
        'latest_date': {'correct': 0, 'total': 0},
        'latest_reason': {'correct': 0, 'total': 0},
        'table_title': {'correct': 0, 'total': 0}
    }
    
    print(f"📁 Total Files Processed: {total_files}")
    print("\n🔍 DETAILED ANALYSIS BY FILE:")
    print("-" * 80)
    
    for result in results:
        filename = result['file_name']
        print(f"\n📄 {filename}")
        
        if filename in EXPECTED_RESULTS:
            expected = EXPECTED_RESULTS[filename]
            file_score = 0
            file_total = 0
            
            for field in ['drawing_title', 'drawing_number', 'revision', 'latest_revision', 'latest_date', 'latest_reason', 'table_title']:
                extracted = result.get(field, '').strip()
                expected_val = expected.get(field, '').strip()
                
                # Normalize for comparison
                extracted_norm = extracted.replace('Ã§', 'ç') if extracted else ''
                expected_norm = expected_val if expected_val else ''
                
                total_fields += 1
                file_total += 1
                field_accuracy[field]['total'] += 1
                
                if extracted_norm == expected_norm:
                    correct_fields += 1
                    file_score += 1
                    field_accuracy[field]['correct'] += 1
                    status = "✅ CORRECT"
                else:
                    status = "❌ INCORRECT"
                
                print(f"  {field:15}: {status}")
                if extracted_norm != expected_norm:
                    print(f"    Expected: '{expected_norm}'")
                    print(f"    Got:      '{extracted_norm}'")
            
            accuracy = (file_score / file_total) * 100
            print(f"  📊 File Accuracy: {file_score}/{file_total} ({accuracy:.1f}%)")
        
        else:
            print("  ⚠️  No expected results defined for this file")
    
    # Overall statistics
    print("\n" + "=" * 80)
    print("📈 OVERALL STATISTICS")
    print("=" * 80)
    
    overall_accuracy = (correct_fields / total_fields) * 100 if total_fields > 0 else 0
    print(f"🎯 Overall Accuracy: {correct_fields}/{total_fields} ({overall_accuracy:.1f}%)")
    
    print(f"\n📊 FIELD-BY-FIELD ACCURACY:")
    for field, stats in field_accuracy.items():
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            print(f"  {field:15}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
    
    # Identify critical issues
    print(f"\n🚨 CRITICAL ISSUES IDENTIFIED:")
    critical_issues = []
    
    for field, stats in field_accuracy.items():
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            if accuracy < 50:
                critical_issues.append(f"{field} ({accuracy:.1f}% accuracy)")
    
    if critical_issues:
        for issue in critical_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ No critical issues found!")
    
    # Success analysis
    print(f"\n🎉 SUCCESS ANALYSIS:")
    success_fields = []
    
    for field, stats in field_accuracy.items():
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            if accuracy >= 80:
                success_fields.append(f"{field} ({accuracy:.1f}% accuracy)")
    
    if success_fields:
        for success in success_fields:
            print(f"  ✅ {success}")
    else:
        print("  ⚠️  No fields achieving 80%+ accuracy")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if field_accuracy['drawing_title']['correct'] / field_accuracy['drawing_title']['total'] < 0.5:
        print("  🔧 Improve title extraction - focus on multi-line title detection")
    
    if field_accuracy['revision']['correct'] / field_accuracy['revision']['total'] < 0.5:
        print("  🔧 Improve current revision detection in title blocks")
    
    if field_accuracy['latest_revision']['correct'] / field_accuracy['latest_revision']['total'] < 0.5:
        print("  🔧 Enhance revision table parsing for N0 revisions")
    
    if field_accuracy['drawing_number']['correct'] / field_accuracy['drawing_number']['total'] < 0.8:
        print("  🔧 Refine drawing number extraction patterns")
    
    print(f"\n🎯 PRODUCTION READINESS:")
    if overall_accuracy >= 90:
        print("  🚀 READY FOR PRODUCTION - High accuracy achieved!")
    elif overall_accuracy >= 70:
        print("  ⚠️  NEEDS MINOR FIXES - Good accuracy but room for improvement")
    else:
        print("  🔧 NEEDS MAJOR IMPROVEMENTS - Accuracy too low for production")
    
    return overall_accuracy, field_accuracy

if __name__ == "__main__":
    analyze_extraction_results()