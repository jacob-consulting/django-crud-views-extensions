from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from typeahead.models import Task, Team

FIRST = [
    "Anna", "Ben", "Clara", "David", "Emma", "Felix", "Greta", "Hannah", "Jonas", "Lea",
    "Lukas", "Marie", "Noah", "Paul", "Sophie", "Tim", "Julia", "Max", "Laura", "Finn",
    "Mia", "Elias", "Lina", "Leon", "Ida", "Emil", "Nora", "Theo", "Ella", "Oskar",
]  # fmt: skip
LAST = [
    "Becker", "Braun", "Fischer", "Hartmann", "Hoffmann", "Koch", "Krüger", "Lange", "Meyer", "Müller",
    "Neumann", "Richter", "Schmidt", "Schneider", "Schröder", "Schulz", "Schwarz", "Wagner", "Weber", "Wolf",
    "Zimmermann", "Krause", "Lehmann", "Werner", "Schmitt", "Schmid", "Köhler", "Maier", "Herrmann", "König",
    "Walter", "Mayer", "Huber", "Kaiser", "Fuchs", "Peters", "Lang", "Scholz", "Möller", "Weiß",
    "Jung", "Hahn", "Schubert", "Vogel", "Friedrich", "Keller", "Günther", "Frank", "Berger", "Winkler",
]  # fmt: skip
USERS = 3000
TEAMS = ["Data", "Mobile", "Payments", "Platform"]
TEAM_SIZE = 500
TEAM_STRIDE = 400  # overlapping slices: some users are in two teams
TASKS = ["Fix login", "Write docs", "Review release", "Update dependencies", "Plan sprint"]


def seed():
    users = seed_users()
    seed_teams(users)


def seed_users() -> list[int]:
    User = get_user_model()
    if not User.objects.filter(username__startswith="demo-").exists():
        password = make_password(None)  # unusable: demo users cannot log in
        User.objects.bulk_create(
            User(
                username=f"demo-{i:04d}",
                first_name=FIRST[i % len(FIRST)],
                last_name=LAST[(i // len(FIRST)) % len(LAST)],
                password=password,
            )
            for i in range(USERS)
        )
    return list(User.objects.filter(username__startswith="demo-").order_by("username").values_list("pk", flat=True))


def seed_teams(users: list[int]):
    if Team.objects.exists():
        return
    for n, name in enumerate(TEAMS):
        team = Team.objects.create(name=name)
        members = users[n * TEAM_STRIDE : n * TEAM_STRIDE + TEAM_SIZE]
        team.members.add(*members)
        for j, title in enumerate(TASKS):
            Task.objects.create(team=team, title=title, assignee_id=members[j * 37] if j % 2 == 0 else None)
