import pytest
from django.conf import settings
from django.template import Context, Template
from django.utils.timezone import now

from pretix.base.models import Event, Organizer
from pretix.multidomain.models import KnownDomain


@pytest.fixture
def env():
    o = Organizer.objects.create(name='MRMCD', slug='mrmcd')
    event = Event.objects.create(
        organizer=o, name='MRMCD2015', slug='2015',
        date_from=now()
    )
    settings.SITE_URL = 'http://example.com'
    return o, event


@pytest.mark.django_db
def test_control_only_on_main_domain(env, client):
    KnownDomain.objects.create(domainname='foobar', organizer=env[0])
    r = client.get('/control/login', HTTP_HOST='foobar')
    assert r.status_code == 302
    assert r['Location'] == 'http://example.com/control/login'


@pytest.mark.django_db
def test_unknown_domain(env, client):
    r = client.get('/control/login', HTTP_HOST='foobar')
    assert r.status_code == 400


@pytest.mark.django_db
def test_event_on_custom_domain(env, client):
    KnownDomain.objects.create(domainname='foobar', organizer=env[0])
    r = client.get('/2015/', HTTP_HOST='foobar')
    assert r.status_code == 200


@pytest.mark.django_db
def test_event_with_custom_domain_on_main_domain(env, client):
    KnownDomain.objects.create(domainname='foobar', organizer=env[0])
    r = client.get('/mrmcd/2015/', HTTP_HOST='example.com')
    assert r.status_code == 302
    assert r['Location'] == 'http://foobar/2015/'


@pytest.mark.django_db
def test_event_on_custom_domain_only_with_wrong_organizer(env, client):
    organizer2 = Organizer.objects.create(name='Dummy', slug='dummy')
    Event.objects.create(
        organizer=organizer2, name='D1234', slug='1234',
        date_from=now()
    )
    KnownDomain.objects.create(domainname='foobar', organizer=env[0])
    r = client.get('/dummy/1234/', HTTP_HOST='foobar')
    assert r.status_code == 404


@pytest.mark.django_db
def test_unknown_event_on_custom_domain(env, client):
    organizer2 = Organizer.objects.create(name='Dummy', slug='dummy')
    Event.objects.create(
        organizer=organizer2, name='D1234', slug='1234',
        date_from=now()
    )
    KnownDomain.objects.create(domainname='foobar', organizer=env[0])
    r = client.get('/1234/', HTTP_HOST='foobar')
    assert r.status_code == 404


@pytest.mark.django_db
def test_cookie_domain_on_custom_domain(env, client):
    KnownDomain.objects.create(domainname='foobar', organizer=env[0])
    r = client.get('/2015/', HTTP_HOST='foobar')
    assert r.status_code == 200
    assert r.client.cookies['pretix_csrftoken']['domain'] == 'foobar'
    assert r.client.cookies['pretix_session']['domain'] == 'foobar'


@pytest.mark.django_db
def test_cookie_domain_on_main_domain(env, client):
    r = client.get('/mrmcd/2015/', HTTP_HOST='example.com')
    assert r.status_code == 200
    assert r.client.cookies['pretix_csrftoken']['domain'] == 'example.com'
    assert r.client.cookies['pretix_session']['domain'] == 'example.com'
