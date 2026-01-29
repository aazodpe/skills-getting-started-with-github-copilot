"""
Tests for the FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_participants():
    """Reset participants before each test"""
    for activity in app.state.__dict__.get('activities', {}).values():
        activity['participants'] = []
    # Clear default participants from activities
    from src.app import activities
    activities["Chess Club"]["participants"] = []
    activities["Programming Class"]["participants"] = []
    activities["Gym Class"]["participants"] = []
    yield


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Soccer Team" in data
    assert "Basketball Club" in data
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data


def test_get_activities_structure(client):
    """Test the structure of activity data"""
    response = client.get("/activities")
    data = response.json()
    
    # Check Soccer Team structure
    soccer = data["Soccer Team"]
    assert "description" in soccer
    assert "schedule" in soccer
    assert "max_participants" in soccer
    assert "participants" in soccer
    assert isinstance(soccer["participants"], list)


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    email = "test@mergington.edu"
    activity = "Soccer Team"
    
    response = client.post(
        f"/activities/{activity}/signup?email={email}",
        follow_redirects=False
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity in data["message"]


def test_signup_adds_participant(client):
    """Test that signup adds participant to activity"""
    email = "student@mergington.edu"
    activity = "Basketball Club"
    
    # Signup
    response = client.post(
        f"/activities/{activity}/signup?email={email}"
    )
    assert response.status_code == 200
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]


def test_signup_duplicate_email(client):
    """Test that duplicate email signup fails"""
    email = "duplicate@mergington.edu"
    activity = "Art Club"
    
    # First signup
    response1 = client.post(
        f"/activities/{activity}/signup?email={email}"
    )
    assert response1.status_code == 200
    
    # Second signup with same email
    response2 = client.post(
        f"/activities/{activity}/signup?email={email}"
    )
    assert response2.status_code == 400
    data = response2.json()
    assert "already signed up" in data["detail"]


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    email = "test@mergington.edu"
    activity = "Nonexistent Activity"
    
    response = client.post(
        f"/activities/{activity}/signup?email={email}"
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]


def test_unregister_success(client):
    """Test successful unregister from activity"""
    email = "unregister@mergington.edu"
    activity = "Drama Society"
    
    # First signup
    client.post(f"/activities/{activity}/signup?email={email}")
    
    # Then unregister
    response = client.post(
        f"/activities/{activity}/unregister?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered" in data["message"]


def test_unregister_removes_participant(client):
    """Test that unregister removes participant from activity"""
    email = "remove@mergington.edu"
    activity = "Mathletes"
    
    # Signup
    client.post(f"/activities/{activity}/signup?email={email}")
    
    # Verify participant exists
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]
    
    # Unregister
    client.post(f"/activities/{activity}/unregister?email={email}")
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity]["participants"]


def test_unregister_not_registered(client):
    """Test unregister for user not registered"""
    email = "not_registered@mergington.edu"
    activity = "Debate Club"
    
    response = client.post(
        f"/activities/{activity}/unregister?email={email}"
    )
    assert response.status_code == 400
    data = response.json()
    assert "not registered" in data["detail"]


def test_unregister_activity_not_found(client):
    """Test unregister from non-existent activity"""
    email = "test@mergington.edu"
    activity = "Nonexistent Activity"
    
    response = client.post(
        f"/activities/{activity}/unregister?email={email}"
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]


def test_max_participants_not_enforced_in_signup(client):
    """Test that current implementation doesn't enforce max participants"""
    activity = "Chess Club"
    max_participants = 12
    
    # Add more participants than max
    for i in range(max_participants + 5):
        email = f"student{i}@mergington.edu"
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
    
    # Verify all were added (no max enforcement)
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert len(activities[activity]["participants"]) == max_participants + 5


def test_activity_details_available(client):
    """Test that all activity details are correctly returned"""
    response = client.get("/activities")
    data = response.json()
    
    # Test one activity in detail
    programming = data["Programming Class"]
    assert programming["description"] == "Learn programming fundamentals and build software projects"
    assert programming["schedule"] == "Tuesdays and Thursdays, 3:30 PM - 4:30 PM"
    assert programming["max_participants"] == 20
