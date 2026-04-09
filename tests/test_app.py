"""
Tests for the High School Management System API

This module contains comprehensive tests for the FastAPI application,
including tests for GET /activities, POST signup, DELETE unregister,
and edge cases like duplicates and not found scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def original_activities():
    """Store original activities state"""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Basketball Team": {"description": "Sports", "schedule": "Mon", "max_participants": 15, "participants": []},
        "Swimming Club": {"description": "Sports", "schedule": "Tue", "max_participants": 20, "participants": []},
        "Art Studio": {"description": "Art", "schedule": "Wed", "max_participants": 15, "participants": []},
        "Drama Club": {"description": "Art", "schedule": "Thu", "max_participants": 25, "participants": []},
        "Debate Team": {"description": "Intellectual", "schedule": "Fri", "max_participants": 16, "participants": []},
        "Science Club": {"description": "Intellectual", "schedule": "Sat", "max_participants": 20, "participants": []},
        "Soccer Team": {"description": "Sports", "schedule": "Wed", "max_participants": 22, "participants": []},
        "Tennis Club": {"description": "Sports", "schedule": "Thu", "max_participants": 12, "participants": []},
        "Music Band": {"description": "Art", "schedule": "Mon", "max_participants": 18, "participants": []},
        "Photography Club": {"description": "Art", "schedule": "Tue", "max_participants": 15, "participants": []},
        "Math Olympiad": {"description": "Intellectual", "schedule": "Wed", "max_participants": 20, "participants": []},
        "Robotics Club": {"description": "Intellectual", "schedule": "Sat", "max_participants": 16, "participants": []}
    }


@pytest.fixture(autouse=True)
def reset_activities(original_activities):
    """Reset activities to original state before each test"""
    # Clear current activities
    activities.clear()
    # Restore original activities with fresh participant lists
    for activity_name, activity_data in original_activities.items():
        activities[activity_name] = {
            "description": activity_data["description"],
            "schedule": activity_data["schedule"],
            "max_participants": activity_data["max_participants"],
            "participants": deepcopy(activity_data["participants"])
        }
    yield
    # No need to clean up as the next test will reset


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        # Verify structure of returned activities
        assert "Chess Club" in data
        assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
        assert "participants" in data["Chess Club"]
        assert isinstance(data["Chess Club"]["participants"], list)

    def test_get_activities_contains_expected_fields(self, client):
        """Test that each activity contains all expected fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data

    def test_get_activities_participants_list(self, client):
        """Test that participants are returned as a list"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "john@mergington.edu"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Signed up john@mergington.edu for Chess Club"
        # Verify participant was added
        assert "john@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_multiple_activities(self, client):
        """Test that a student can signup for multiple activities"""
        email = "student@mergington.edu"
        # Sign up for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        # Sign up for second activity
        response2 = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Basketball Team"]["participants"]

    def test_signup_duplicate_email_returns_400(self, client):
        """Test that duplicate signup returns 400 error"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up"
        # Verify participant list wasn't modified
        assert activities["Chess Club"]["participants"].count(email) == 1

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Non Existent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_with_empty_email(self, client):
        """Test signup with empty email string"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        assert response.status_code == 200
        assert "" in activities["Chess Club"]["participants"]

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        email = "student+tag@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities["Chess Club"]["participants"]

    def test_signup_case_sensitive_activity_name(self, client):
        """Test that activity names are case-sensitive"""
        response = client.post(
            "/activities/chess club/signup",  # lowercase
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from Chess Club"
        # Verify participant was removed
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Non Existent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_participant_not_found_returns_404(self, client):
        """Test that unregistering non-participant returns 404"""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "nonexistent@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

    def test_unregister_from_empty_activity(self, client):
        """Test unregister from activity with no participants"""
        response = client.delete(
            "/activities/Basketball Team/signup",  # Has no participants initially
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

    def test_unregister_then_signup_again(self, client):
        """Test that a student can signup again after unregistering"""
        email = "test@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Unregister
        response2 = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        assert email not in activities[activity]["participants"]
        
        # Sign up again
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        assert email in activities[activity]["participants"]

    def test_unregister_case_sensitive_activity_name(self, client):
        """Test that activity names are case-sensitive for unregister"""
        response = client.delete(
            "/activities/chess club/signup",  # lowercase
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestIntegration:
    """Integration tests for combined operations"""

    def test_signup_and_unregister_flow(self, client):
        """Test complete signup and unregister flow"""
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Verify email not in activity
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify email in activity
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify email not in activity
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_students_signup_for_same_activity(self, client):
        """Test multiple students signing up for the same activity"""
        activity = "Science Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all students are in the activity
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants

    def test_participant_count_accuracy(self, client):
        """Test that participant count remains accurate through signup/unregister"""
        activity = "Art Studio"
        initial_count = len(activities[activity]["participants"])
        
        # Sign up 3 students
        for i in range(3):
            email = f"student{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify count
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 3
        
        # Unregister 2 students
        for i in range(2):
            email = f"student{i}@mergington.edu"
            response = client.delete(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify count
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1