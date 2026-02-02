import requests
import re
from urllib.parse import urlparse

class CredibilityChecker:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    def check_website(self, url):
        '''Main function to check website credibility'''
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        results = {
            'url': url,
            'trust_score': 0,
            'checks': {},
            'summary': 'Analysis failed'
        }
        
        try:
            # Fetch website content
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=10)
            content = response.text
            
            # Check 1: HTTPS
            https_result = self.check_https(url)
            results['checks']['https'] = https_result
            
            # Check 2: Contact Info (detailed search)
            contact_result = self.check_contact_info(content)
            results['checks']['contact_info'] = contact_result
            
            # Check 3: Content Quality
            content_result = self.check_content_quality(content)
            results['checks']['content_quality'] = content_result
            
            # Check 4: Suspicious Patterns (detailed)
            suspicious_result = self.check_suspicious_patterns(content, url)
            results['checks']['suspicious_patterns'] = suspicious_result
            
            # Calculate Trust Score
            results['trust_score'] = self.calculate_trust_score(results['checks'])
            
            # Generate summary
            results['summary'] = self.generate_summary(results)
            
        except Exception as e:
            results['error'] = f'Cannot analyze website: {str(e)}'
        
        return results
    
    def check_https(self, url):
        '''Check if website uses HTTPS'''
        is_https = url.startswith('https://')
        
        return {
            'status': 'Secure' if is_https else 'Not Secure',
            'secure': is_https,
            'score': 30 if is_https else 0,
            'message': '✅ Using HTTPS (Secure connection)' if is_https else '❌ Not using HTTPS (Potential security risk)',
            'details': [
                'HTTPS encrypts data between your browser and the website, preventing eavesdropping and tampering.' if is_https 
                else 'HTTP connections are not encrypted. Sensitive information like passwords can be intercepted.'
            ]
        }
    
    def check_contact_info(self, content):
        '''Check for contact information with detailed extraction'''
        text = content.lower()
        
        # Extract actual email addresses
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails_found = re.findall(email_pattern, content)
        emails_found = list(set(emails_found))[:3]  # Get unique emails, max 3
        
        # Extract phone numbers (various formats)
        phone_patterns = [
            r'\+\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',  # International
            r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',  # (123) 456-7890
            r'\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{4}',  # 123-456-7890
        ]
        
        phones_found = []
        for pattern in phone_patterns:
            phones = re.findall(pattern, content)
            phones_found.extend(phones)
        phones_found = list(set(phones_found))[:3]  # Get unique phones, max 3
        
        # Look for address indicators
        address_keywords = ['street', 'avenue', 'road', 'lane', 'boulevard', 'drive', 
                           'city', 'state', 'zip', 'postal', 'address:', 'location:']
        address_found = any(keyword in text for keyword in address_keywords)
        
        # Look for contact page links
        contact_page_patterns = ['contact', 'about', 'support', 'help', 'reach us']
        contact_pages = []
        for pattern in contact_page_patterns:
            if re.search(f'href=[^>]*{pattern}[^>]*', text, re.IGNORECASE):
                contact_pages.append(f'"{pattern}" page found')
        
        # Calculate score
        score = 0
        details_list = []
        
        if emails_found:
            score += 15
            details_list.append(f'✅ Found {len(emails_found)} email address(es)')
            for email in emails_found[:2]:  # Show first 2 emails
                details_list.append(f'   • {email}')
        else:
            details_list.append('❌ No email addresses found')
        
        if phones_found:
            score += 10
            details_list.append(f'✅ Found {len(phones_found)} phone number(s)')
            for phone in phones_found[:2]:  # Show first 2 phones
                details_list.append(f'   • {phone}')
        else:
            details_list.append('❌ No phone numbers found')
        
        if address_found:
            score += 5
            details_list.append('✅ Address information detected on the page')
        else:
            details_list.append('❌ No address information found')
        
        if contact_pages:
            score += 5
            details_list.append(f'✅ Found contact pages: {", ".join(contact_pages)}')
        else:
            details_list.append('❌ No dedicated contact pages found')
        
        status = 'Good' if score >= 20 else 'Fair' if score >= 10 else 'Poor'
        
        return {
            'status': status,
            'score': score,
            'has_email': len(emails_found) > 0,
            'has_phone': len(phones_found) > 0,
            'has_address': address_found,
            'emails_found': emails_found,
            'phones_found': phones_found,
            'contact_pages': contact_pages,
            'message': f'Contact Information: {status} ({score}/35 points)',
            'details': details_list
        }
    
    def check_content_quality(self, content):
        '''Analyze content quality with detailed metrics'''
        # Extract text between tags
        text = re.sub('<[^>]+>', ' ', content)
        words = text.split()
        word_count = len(words)
        
        # Count sentences
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if len(s.strip()) > 0])
        
        # Calculate average word length
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Check for grammar indicators
        has_capitalization = sum(1 for char in text[:1000] if char.isupper()) > 50
        has_punctuation = text.count('.') + text.count('!') + text.count('?') > 10
        
        # Calculate score with detailed breakdown
        score = 0
        details_list = []
        
        if word_count > 500:
            score += 15
            details_list.append(f'✅ Substantial content: {word_count} words')
        elif word_count > 200:
            score += 10
            details_list.append(f'⚠️ Moderate content: {word_count} words')
        elif word_count > 50:
            score += 5
            details_list.append(f'⚠️ Limited content: {word_count} words')
        else:
            details_list.append(f'❌ Very little content: {word_count} words')
        
        if sentence_count > 10:
            score += 5
            details_list.append(f'✅ Good sentence structure: {sentence_count} sentences')
        else:
            details_list.append(f'⚠️ Few sentences: {sentence_count} sentences')
        
        if has_capitalization and has_punctuation:
            score += 5
            details_list.append('✅ Proper capitalization and punctuation detected')
        elif has_capitalization or has_punctuation:
            score += 2
            details_list.append('⚠️ Some formatting issues detected')
        else:
            details_list.append('❌ Poor formatting (missing capitalization/punctuation)')
        
        details_list.append(f'📊 Average word length: {round(avg_word_length, 1)} characters')
        
        status = 'Good' if score >= 15 else 'Fair' if score >= 10 else 'Poor'
        
        return {
            'status': status,
            'score': score,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_word_length': round(avg_word_length, 1),
            'message': f'Content Quality: {status} ({score}/25 points)',
            'details': details_list
        }
    
    def check_suspicious_patterns(self, content, url):
        '''Look for scam patterns with detailed explanations'''
        text = content.lower()
        url_lower = url.lower()
        score = 40
        indicators = []
        detailed_explanations = []
        
        # Define suspicious patterns with explanations
        scam_patterns = {
            'you have won|you won|congratulations.*winner': {
                'risk': 'High',
                'explanation': 'Common lottery/scam language targeting victims'
            },
            'free.*money|free.*gift|free.*prize': {
                'risk': 'High', 
                'explanation': '"Free money" offers often lead to scams or hidden costs'
            },
            'click here|click below|click now': {
                'risk': 'Medium',
                'explanation': 'Excessive "click" commands can indicate phishing attempts'
            },
            'limited time offer|act now|don\'t miss out': {
                'risk': 'Medium',
                'explanation': 'Urgency tactics used to prevent careful consideration'
            },
            'risk-free|guaranteed.*profit|money.*back': {
                'risk': 'High',
                'explanation': 'Unrealistic guarantees common in financial scams'
            },
            'wire transfer|western union|money gram|bitcoin.*send': {
                'risk': 'High',
                'explanation': 'Irreversible payment methods favored by scammers'
            },
            'password.*verify|account.*suspended|urgent.*action': {
                'risk': 'Critical',
                'explanation': 'Phishing attempts to steal login credentials'
            },
            'dear friend|dear customer|dear winner': {
                'risk': 'Medium',
                'explanation': 'Impersonal greetings common in mass scam emails'
            },
            'inheritance.*claim|unclaimed.*money|government.*grant': {
                'risk': 'High',
                'explanation': 'Fake inheritance/grant scams requesting upfront fees'
            },
            'miracle.*cure|lose.*weight.*fast|anti-aging.*secret': {
                'risk': 'Medium',
                'explanation': 'Health scams with unrealistic claims'
            }
        }
        
        # Check each pattern
        for pattern, info in scam_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                indicators.append(pattern.split('|')[0])
                detailed_explanations.append(f"⚠️ {info['risk']} Risk: {info['explanation']}")
                if info['risk'] == 'Critical':
                    score -= 5
                elif info['risk'] == 'High':
                    score -= 4
                else:
                    score -= 2
        
        # Check for excessive special characters
        if text.count('!') > 20:
            indicators.append('Excessive exclamation marks')
            detailed_explanations.append('⚠️ Medium Risk: Overuse of "!" suggests aggressive marketing or scams')
            score -= 3
        
        if text.count('$') > 15:
            indicators.append('Excessive dollar signs')
            detailed_explanations.append('⚠️ Medium Risk: Focus on money can indicate get-rich-quick schemes')
            score -= 3
        
        # Check URL for suspicious patterns
        if re.search(r'\d{10,}', url_lower):
            indicators.append('Suspicious numbers in URL')
            detailed_explanations.append('⚠️ High Risk: Long number sequences in URLs often indicate temporary/scam sites')
            score -= 5
        
        # Check for hidden text (common in spam)
        hidden_patterns = ['display:\s*none', 'visibility:\s*hidden', 'opacity:\s*0']
        hidden_count = sum(text.count(pattern) for pattern in hidden_patterns)
        if hidden_count > 5:
            indicators.append('Hidden text/elements')
            detailed_explanations.append(f'⚠️ High Risk: {hidden_count} hidden elements detected (common in SEO spam)')
            score -= 4
        
        # Check for excessive popup scripts
        if text.count('alert(') > 3 or text.count('popup') > 5:
            indicators.append('Excessive popups/alerts')
            detailed_explanations.append('⚠️ Medium Risk: Too many popups can indicate aggressive advertising')
            score -= 3
        
        # Check domain age patterns (basic)
        suspicious_domains = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz']
        if any(domain in url_lower for domain in suspicious_domains):
            indicators.append('Suspicious domain extension')
            detailed_explanations.append('⚠️ High Risk: Free domain extensions often used for temporary/scam sites')
            score -= 4
        
        score = max(0, score)
        
        # Determine status
        if score >= 35:
            status = 'Safe'
        elif score >= 25:
            status = 'Suspicious'
        else:
            status = 'High Risk'
        
        # If no issues found
        if not indicators:
            detailed_explanations.append('✅ No major suspicious patterns detected')
            detailed_explanations.append('✅ Website appears to use standard marketing language')
        else:
            detailed_explanations.insert(0, f'Found {len(indicators)} suspicious indicators:')
            for i, indicator in enumerate(indicators[:5], 1):
                detailed_explanations.insert(i, f'   • {indicator}')
        
        return {
            'status': status,
            'score': score,
            'indicators': indicators[:10],
            'indicator_count': len(indicators),
            'message': f'Safety Check: {status} ({len(indicators)} suspicious indicators found)',
            'details': detailed_explanations,
            'risk_level': 'Low' if score >= 35 else 'Medium' if score >= 25 else 'High'
        }
    
    def calculate_trust_score(self, checks):
        '''Calculate overall trust score'''
        total = 0
        total += checks['https']['score']
        total += checks['contact_info']['score']
        total += checks['content_quality']['score']
        total += checks['suspicious_patterns']['score']
        
        # Convert to percentage (max score = 30 + 35 + 25 + 40 = 130)
        return min(100, int((total / 130) * 100))
    
    def generate_summary(self, results):
        '''Generate summary'''
        score = results['trust_score']
        
        if score >= 80:
            return '✅ This website appears highly credible!'
        elif score >= 60:
            return '⚠️ This website has moderate credibility. Exercise caution.'
        elif score >= 40:
            return '⚠️ This website has low credibility. Be careful.'
        else:
            return '❌ This website appears suspicious. Avoid sharing personal information.'

# Test the checker
if __name__ == '__main__':
    print('Testing Credibility Checker...')
    checker = CredibilityChecker()
    result = checker.check_website('https://www.wikipedia.org')
    print(f'Trust Score: {result.get("trust_score", "N/A")}')
    print(f'Summary: {result.get("summary", "N/A")}')
    print('\nDetailed Contact Info:')
    if 'contact_info' in result.get('checks', {}):
        for detail in result['checks']['contact_info'].get('details', []):
            print(f'  {detail}')
    print('\nSuspicious Patterns:')
    if 'suspicious_patterns' in result.get('checks', {}):
        for detail in result['checks']['suspicious_patterns'].get('details', []):
            print(f'  {detail}')