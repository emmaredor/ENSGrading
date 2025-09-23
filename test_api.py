"""
Test script to debug the API response
"""
import requests
import json
import yaml
import base64

# Test data
student_info = {
    'firstname': 'Test',
    'name': 'Student',
    'email': 'test@example.com',
    'birthdate': '1990-01-01',
    'birthplace': 'Test City',
    'student_number': '12345'
}

author_info = {
    'firstname': 'Test',
    'name': 'Author',
    'title': 'Test Title',
    'email': 'author@example.com'
}

grades_data = [
    {
        'semester': 'S1',
        'course': 'Test Course',
        'grade': '15',
        'ects': '6',
        'status': 'Validé'
    }
]

def test_single_api():
    url = 'http://localhost:8080/api/single'
    
    # Prepare files
    files = {
        'student_info': ('student_info.yaml', yaml.dump(student_info), 'application/x-yaml'),
        'author_info': ('author_info.yaml', yaml.dump(author_info), 'application/x-yaml'),
        'grades': ('grades.json', json.dumps(grades_data), 'application/json')
    }
    
    try:
        print("Testing API...")
        response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response keys: {result.keys()}")
            
            if 'pdf_data' in result:
                print(f"PDF data length: {len(result['pdf_data'])}")
                print(f"PDF data starts with: {result['pdf_data'][:50]}...")
                
                # Test base64 decode
                try:
                    pdf_bytes = base64.b64decode(result['pdf_data'])
                    print(f"Decoded PDF size: {len(pdf_bytes)} bytes")
                    print(f"PDF header: {pdf_bytes[:10]}")
                    
                    # Save test file
                    with open('test_output.pdf', 'wb') as f:
                        f.write(pdf_bytes)
                    print("Test PDF saved as test_output.pdf")
                    
                except Exception as e:
                    print(f"Base64 decode error: {e}")
            
            if 'filename' in result:
                print(f"Filename: {result['filename']}")
                
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == '__main__':
    test_single_api()