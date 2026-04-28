# checkins/analysis.py

from textblob import TextBlob

# Blocker keywords for detection
BLOCKER_KEYWORDS = {
    'API': ['api', 'endpoint', 'request', 'timeout', 'error 5', 'crash'],
    'DESIGN': ['design', 'ui', 'ux', 'layout', 'color', 'component'],
    'TEAM': ['team', 'communication', 'conflict', 'meeting', 'sync', 'blocked by'],
    'BACKEND': ['database', 'query', 'server', 'deployment', 'docker'],
    'DOCUMENTATION': ['doc', 'wiki', 'readme', 'guide', 'unclear'],
    'DEPENDENCY': ['dependency', 'package', 'version', 'upgrade', 'incompatible'],
    'PERFORMANCE': ['slow', 'lag', 'timeout', 'performance', 'memory', 'cpu'],
    'TESTING': ['test', 'coverage', 'bug', 'qa', 'regression'],
}

ENERGY_KEYWORDS = {
    'high': ['excited', 'great', 'amazing', 'awesome', 'love', 'perfect', 'excellent'],
    'medium': ['good', 'nice', 'fine', 'okay', 'alright', 'decent'],
    'low': ['tired', 'exhausted', 'burnt out', 'drained', 'overwhelmed'],
}


def analyze_checkin_response(answer_text):
    """
    Perform sentiment and blocker analysis on check-in response
    
    Returns:
        dict with analysis data
    """
    
    if not answer_text:
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'NEUTRAL',
            'has_blocker': False,
            'blocker_types': [],
            'blocker_text': '',
            'energy_level': 5,
            'ai_summary': 'No response provided.',
        }
    
    # 1. SENTIMENT ANALYSIS
    blob = TextBlob(answer_text.lower())
    sentiment_score = blob.sentiment.polarity  # -1 to 1
    
    if sentiment_score > 0.1:
        sentiment_label = 'POSITIVE'
    elif sentiment_score < -0.1:
        sentiment_label = 'NEGATIVE'
    else:
        sentiment_label = 'NEUTRAL'
    
    # 2. BLOCKER DETECTION
    text_lower = answer_text.lower()
    detected_blockers = []
    
    for blocker_type, keywords in BLOCKER_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_blockers.append(blocker_type)
    
    has_blocker = len(detected_blockers) > 0
    
    # Extract blocker sentences
    blocker_text = ''
    if has_blocker:
        sentences = answer_text.split('.')
        blocker_sentences = [
            s.strip() for s in sentences 
            if any(keyword in s.lower() for blocker_type in detected_blockers 
                   for keyword in BLOCKER_KEYWORDS[blocker_type])
        ]
        blocker_text = ' '.join(blocker_sentences[:2])
    
    # 3. ENERGY LEVEL DETECTION
    energy_level = 5
    
    for energy_keyword in ENERGY_KEYWORDS['high']:
        if energy_keyword in text_lower:
            energy_level = 9
            break
    
    for energy_keyword in ENERGY_KEYWORDS['low']:
        if energy_keyword in text_lower:
            energy_level = 2
            break
    
    if energy_level == 5:
        for energy_keyword in ENERGY_KEYWORDS['medium']:
            if energy_keyword in text_lower:
                energy_level = 6
                break
    
    # 4. AUTO-GENERATED SUMMARY
    ai_summary = generate_summary(answer_text, detected_blockers)
    
    return {
        'sentiment_score': round(sentiment_score, 2),
        'sentiment_label': sentiment_label,
        'has_blocker': has_blocker,
        'blocker_types': detected_blockers,
        'blocker_text': blocker_text,
        'energy_level': energy_level,
        'ai_summary': ai_summary,
    }


def generate_summary(text, blockers):
    """Generate concise summary of check-in response"""
    sentences = text.split('.')
    main_sentence = sentences[0].strip() if sentences else text
    
    if len(main_sentence) > 100:
        main_sentence = main_sentence[:97] + '...'
    
    if blockers:
        return f"{main_sentence} [Blockers: {', '.join(blockers)}]"
    
    return main_sentence


def create_analysis_for_answer(checkin_answer):
    """Create CheckinAnalysis record"""
    from checkins.models import CheckinAnalysis
    
    try:
        print(f"🔍 Starting analysis for answer: {checkin_answer.answer_text[:50]}")
        
        analysis_data = analyze_checkin_response(checkin_answer.answer_text)
        print(f"✅ Analysis data generated: {analysis_data}")
        
        analysis, created = CheckinAnalysis.objects.update_or_create(
            checkin_answer=checkin_answer,
            defaults={
                'sentiment_score': analysis_data['sentiment_score'],
                'sentiment_label': analysis_data['sentiment_label'],
                'has_blocker': analysis_data['has_blocker'],
                'blocker_types': analysis_data['blocker_types'],
                'blocker_text': analysis_data['blocker_text'],
                'energy_level': analysis_data['energy_level'],
                'ai_summary': analysis_data['ai_summary'],
            }
        )
        
        print(f"✅ Analysis saved! ID: {analysis.id}, Created: {created}")
        return analysis, created
        
    except Exception as e:
        print(f"❌ ERROR in create_analysis_for_answer: {e}")
        import traceback
        traceback.print_exc()
        return None, False