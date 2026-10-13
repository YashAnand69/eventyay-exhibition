import pytest
from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse
from django_scopes import scopes_disabled
from eventyay.base.models import Team, User

from exhibition.models import ExhibitionRequest, ExhibitionRequestState


@pytest.mark.django_db
@pytest.mark.parametrize("state", list(ExhibitionRequestState))
def test_state_actions_stay_in_state_dropdown(event, settings, state):
    settings.SITE_URL = "https://testserver"
    with scopes_disabled():
        event.plugins = "exhibition"
        event.save(update_fields=["plugins"])
        manager = User.objects.create_user("manager@example.com", "pw")
        team = Team.objects.create(
            organizer=event.organizer, name="Managers", all_events=True, can_change_exhibition_proposals=True
        )
        team.members.add(manager)
        applicant = User.objects.create_user("applicant@example.com", "pw")
        proposal = ExhibitionRequest.objects.create(event=event, user=applicant, name="Acme", state=state)
        actions = proposal.available_review_actions()
    client = Client()
    client.force_login(manager)
    response = client.get(
        reverse(
            "plugins:exhibition:request.list",
            kwargs={
                "organizer": event.organizer.slug,
                "event": event.slug,
            },
        )
    )
    assert response.status_code == 200
    row = BeautifulSoup(response.content, "html.parser").select_one(f'[data-request-row="{proposal.code}"]')
    assert row is not None
    state_cell = row.select_one(".request-state-cell")
    assert [
        item["data-request-action"] for item in state_cell.select(".dropdown-menu [data-request-action]")
    ] == actions
    assert not row.select_one("[data-request-actions-cell]").select("[data-request-action]")
    assert row.select_one("[data-request-actions-cell] a") is not None
    if actions:
        toggle = state_cell.select_one('[data-toggle="dropdown"]')
        assert toggle["aria-haspopup"] == "true"
        assert toggle["aria-expanded"] == "false"
        assert state_cell.select_one(".dropdown-menu") is not None


@pytest.mark.django_db
def test_review_only_user_has_no_state_dropdown(event, settings):
    settings.SITE_URL = "https://testserver"
    with scopes_disabled():
        event.plugins = "exhibition"
        event.save(update_fields=["plugins"])
        reviewer = User.objects.create_user("reviewer@example.com", "pw")
        team = Team.objects.create(
            organizer=event.organizer, name="Reviewers", all_events=True, is_exhibition_reviewer=True
        )
        team.members.add(reviewer)
        applicant = User.objects.create_user("applicant@example.com", "pw")
        proposal = ExhibitionRequest.objects.create(
            event=event, user=applicant, name="Acme", state=ExhibitionRequestState.SUBMITTED
        )
    client = Client()
    client.force_login(reviewer)
    response = client.get(
        reverse(
            "plugins:exhibition:request.list",
            kwargs={
                "organizer": event.organizer.slug,
                "event": event.slug,
            },
        )
    )
    assert response.status_code == 200
    row = BeautifulSoup(response.content, "html.parser").select_one(f'[data-request-row="{proposal.code}"]')
    assert row.select_one("[data-request-state]").text == proposal.get_state_display()
    assert not row.select("[data-request-action]")
    assert row.select_one("[data-request-actions-cell] a") is not None
