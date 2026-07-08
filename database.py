import os
from supabase import create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


def get_user(telegram_id):
    response = (
        supabase
        .table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def add_user(user_id, username, first_name):
    data = {
        "telegram_id": user_id,
        "username": username,
        "first_name": first_name,
        "points": 0,
        "tickets": 0,
        "referrals": 0
    }

    supabase.table("users").insert(data).execute()


def get_points(telegram_id):
    response = (
        supabase
        .table("users")
        .select("points")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if response.data:
        return response.data[0]["points"]

    return 0


def get_tasks():
    response = (
        supabase
        .table("tasks")
        .select("*")
        .eq("active", True)
        .execute()
    )

    return response.data


def complete_task(telegram_id, task_id, points):

    check = (
        supabase
        .table("completed_tasks")
        .select("*")
        .eq("telegram_id", telegram_id)
        .eq("task_id", task_id)
        .execute()
    )

    if check.data:
        return False


    supabase.table("completed_tasks").insert({
        "telegram_id": telegram_id,
        "task_id": task_id
    }).execute()


    user = (
        supabase
        .table("users")
        .select("points")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if not user.data:
        return False

    current_points = user.data[0]["points"]


    supabase.table("users").update({
        "points": current_points + points
    }).eq("telegram_id", telegram_id).execute()


    return True
