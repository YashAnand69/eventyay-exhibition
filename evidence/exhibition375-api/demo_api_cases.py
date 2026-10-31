import pytest
from django.urls import reverse
from django.utils import timezone
from django_scopes import scopes_disabled
from eventyay.base.models import Event, Organizer, Team, User
from exhibition.models import ExhibitorInfo, ExhibitorTag, Lead

@pytest.fixture
def event(db):
    organizer = Organizer.objects.create(name="Test Organizer", slug="test-organizer")
    return Event.objects.create(organizer=organizer, name="Test Event", slug="test-event", live=True, date_from=timezone.now())

def _exhibitor(event, **flags):
    return ExhibitorInfo.objects.create(event=event, name="Acme", **flags)

@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, expected_tags",
    [
        ({"note": "Call next week"}, ["vip"]),
        ({"note": "Call next week", "tags": None}, ["vip"]),
        ({"note": "Call next week", "tags": []}, []),
        ({"note": "Call next week", "tags": ["follow-up"]}, ["follow-up"]),
    ],
    ids=["omitted", "null", "cleared", "replaced"],
)
def test_note_update_only_changes_tags_when_supplied(client, event, payload, expected_tags):
    with scopes_disabled():
        event.plugins = "exhibition"
        event.save()
        user = User.objects.create_user("organizer@example.com", "test-password")
        team = Team.objects.create(organizer=event.organizer, all_events=True, can_change_event_settings=True)
        team.members.add(user)
        client.force_login(user)
        exhibitor = _exhibitor(event, lead_scanning_enabled=True)
        lead = Lead.objects.create(
            exhibitor=exhibitor,
            exhibitor_name="Acme",
            pseudonymization_id="attendee-code",
            scanned=timezone.now(),
            scan_type="qr",
            device_name="phone",
            attendee={"name": "Jane", "note": "Old note", "tags": ["vip"]},
        )
        original_tag = ExhibitorTag.objects.create(exhibitor=exhibitor, name="vip", use_count=3)
        url = reverse(
            "plugins:exhibition:lead-update",
            kwargs={
                "organizer": event.organizer.slug,
                "event": event.slug,
                "lead_id": "attendee-code",
            },
        )
        response = client.post(
            url,
            payload,
            content_type="application/json",
            HTTP_EXHIBITOR=exhibitor.key,
        )
        lead.refresh_from_db()
        original_tag.refresh_from_db()
        print("\nCASE: " + ("omitted" if "tags" not in payload else repr(payload["tags"])), flush=True)
        print("POST " + url + "\nJSON: " + __import__("json").dumps(payload), flush=True)
        print("HTTP " + str(response.status_code) + " | Stored note: " + lead.attendee["note"] + " | Stored tags: " + repr(lead.attendee["tags"]), flush=True)
        print("Expected stored tags: " + repr(expected_tags), flush=True)

    assert response.status_code == 200, response.json()
    assert lead.attendee == {"name": "Jane", "note": "Call next week", "tags": expected_tags}
    assert response.json()["attendee"]["tags"] == lead.attendee["tags"]
    assert original_tag.use_count == 3
