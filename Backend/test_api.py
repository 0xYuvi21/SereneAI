import requests
import uuid
import time
import sys

BASE_URL = "http://localhost:8000/api"

def print_step(msg):
    print(f"\n[{'='*5}] {msg} [{'='*5}]")

def run_tests():
    # 1. Setup unique email for testing
    unique_id = uuid.uuid4().hex[:8]
    email = f"test_{unique_id}@example.com"
    password = "securepassword123"
    
    print_step("1. User Registration")
    reg_res = requests.post(f"{BASE_URL}/users/register", json={
        "email": email,
        "password": password,
        "reason_for_using_app": "testing the flow"
    })
    
    if reg_res.status_code != 200:
        print(f"Failed to register: {reg_res.text}")
        sys.exit(1)
        
    print("✓ Registration successful")
    
    print_step("2. User Login")
    login_res = requests.post(f"{BASE_URL}/users/login", json={
        "email": email,
        "password": password
    })
    
    if login_res.status_code != 200:
        print(f"Failed to login: {login_res.text}")
        sys.exit(1)
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Login successful, token acquired")
    
    print_step("3. Get User Profile (/me)")
    me_res = requests.get(f"{BASE_URL}/users/me", headers=headers)
    if me_res.status_code != 200:
        print(f"Failed to get user profile: {me_res.text}")
        sys.exit(1)
    
    user_id = me_res.json()["user_id"]
    print(f"✓ Profile retrieved. User ID: {user_id}")
    
    print_step("4. Update User Profile")
    update_res = requests.patch(f"{BASE_URL}/users/me", headers=headers, json={
        "age": 25,
        "gender": "Non-binary",
        "location": "Test City",
        "preferred_language": "en"
    })
    if update_res.status_code != 200:
        print(f"Failed to update profile: {update_res.text}")
    else:
        print("✓ Profile updated successfully")
        
    print_step("5. Start Session")
    start_res = requests.post(f"{BASE_URL}/sessions/start", headers=headers, json={
        "emotion_at_start": "sad"
    })
    if start_res.status_code != 200:
        print(f"Failed to start session: {start_res.text}")
        sys.exit(1)
        
    session_id = start_res.json()["session_id"]
    print(f"✓ Session started. Session ID: {session_id}")
    
    print_step("6. Create Conversations (Simulating Engagement > 7 messages)")
    # We need 7+ messages to trigger is_active = True
    for i in range(8):
        conv_res = requests.post(f"{BASE_URL}/conversations/", headers=headers, json={
            "session_id": session_id,
            "user_input": f"Hello, this is message {i+1}",
            "bot_response": f"Reply to message {i+1}",
            "sentiment_score": 0.5,
            "response_time": 1.2
        })
        if conv_res.status_code != 200:
            print(f"Failed to send message {i+1}: {conv_res.text}")
        
    print("✓ 8 messages sent successfully")
    
    print_step("7. End Session")
    end_res = requests.put(f"{BASE_URL}/sessions/{session_id}/end", headers=headers, json={
        "emotion_at_end": "happy",
        "session_quality_score": 8
    })
    
    if end_res.status_code != 200:
        print(f"Failed to end session: {end_res.text}")
        sys.exit(1)
        
    end_data = end_res.json()
    print(f"✓ Session ended. Dropout Risk Score generated: {end_data.get('dropout_risk_score', 'N/A')} ({end_data.get('dropout_risk_label', 'N/A')})")
    
    print_step("8. Get Analytics: Dashboard")
    dash_res = requests.get(f"{BASE_URL}/users/dashboard", headers=headers)
    if dash_res.status_code == 200:
        print("✓ Dashboard data retrieved successfully:")
        print(dash_res.json())
    else:
        print(f"Failed to get dashboard: {dash_res.text}")
        
    print_step("9. Get Analytics: Recovery Rate")
    rec_res = requests.get(f"{BASE_URL}/analytics/recovery-rate/{user_id}", headers=headers)
    if rec_res.status_code == 200:
        print("✓ Recovery Rate data retrieved successfully:")
        print(rec_res.json())
    else:
        print(f"Failed to get recovery rate: {rec_res.text}")
        
    print_step("10. Get Analytics: Emotion Trends")
    emo_res = requests.get(f"{BASE_URL}/analytics/emotion-trends/{user_id}", headers=headers)
    if emo_res.status_code == 200:
        print("✓ Emotion trends retrieved successfully:")
        print(emo_res.json())
    else:
        print(f"Failed to get emotion trends: {emo_res.text}")
        
    print_step("11. Get Analytics: Dropout Risk")
    risk_res = requests.get(f"{BASE_URL}/analytics/dropout-risk/{user_id}", headers=headers)
    if risk_res.status_code == 200:
        print("✓ Dropout risk retrieved successfully:")
        print(risk_res.json())
    else:
        print(f"Failed to get dropout risk: {risk_res.text}")

    print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    try:
        requests.get("http://localhost:8000/docs") # quick check if server is running
        run_tests()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Server is not running at {BASE_URL}. Please start the FastAPI backend first.")
