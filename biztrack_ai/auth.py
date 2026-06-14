"""
Authentication module for BizTrack AI
Handles user signup, login, and session management
"""

import hashlib

from database import db, log_activity, is_unique_violation


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def signup(name, email, password, role='staff'):
    """Register a new user"""
    email = email.strip().lower()
    try:
        hashed_pw = hash_password(password)
        db().table("users").insert({
            "name": name,
            "email": email,
            "password": hashed_pw,
            "role": role,
        }).execute()
        return True, "Account created successfully!"
    except Exception as e:
        if is_unique_violation(e):
            return False, "Email already exists!"
        return False, f"Error: {str(e)}"


def login(email, password):
    """Authenticate user login"""
    email = email.strip().lower()
    hashed_pw = hash_password(password)
    response = (
        db()
        .table("users")
        .select("id, name, email, role")
        .eq("email", email)
        .eq("password", hashed_pw)
        .execute()
    )
    users = response.data or []

    if users:
        user = users[0]
        log_activity(user["id"], "Login", f"User {user['name']} logged in")
        return True, {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
        }
    return False, "Invalid email or password!"


def get_all_users():
    """Get all users (Admin only)"""
    response = (
        db()
        .table("users")
        .select("id, name, email, role, created_at")
        .execute()
    )
    rows = response.data or []
    return [(r["id"], r["name"], r["email"], r["role"], r["created_at"]) for r in rows]


def update_user_role(user_id, new_role):
    """Update user role"""
    db().table("users").update({"role": new_role}).eq("id", user_id).execute()


def delete_user(user_id):
    """Delete a user"""
    db().table("users").delete().eq("id", user_id).execute()


def change_password(user_id, old_password, new_password):
    """Change user password"""
    hashed_old = hash_password(old_password)
    response = (
        db()
        .table("users")
        .select("id")
        .eq("id", user_id)
        .eq("password", hashed_old)
        .execute()
    )
    if not response.data:
        return False, "Current password is incorrect!"

    hashed_new = hash_password(new_password)
    db().table("users").update({"password": hashed_new}).eq("id", user_id).execute()
    return True, "Password changed successfully!"
