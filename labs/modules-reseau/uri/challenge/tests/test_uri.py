"""Tests pytest+testinfra pour le challenge module uri."""

import json

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === GET ===

def test_get_json_file_exists(host):
    f = host.file("/opt/lab-uri-get.json")
    assert f.exists
    assert f.is_file
    assert f.mode == 0o644


def test_get_json_is_valid_json(host):
    content = host.file("/opt/lab-uri-get.json").content_string
    data = json.loads(content)
    # httpbin /json retourne un dict avec une cle "slideshow"
    assert "slideshow" in data, f"Cle 'slideshow' attendue de httpbin /json, vu : {list(data.keys())}"


# === POST ===

def test_post_json_file_exists(host):
    f = host.file("/opt/lab-uri-post.json")
    assert f.exists
    assert f.mode == 0o644


def test_post_response_echoes_body(host):
    """httpbin /post renvoie le body JSON envoye dans le champ 'json'."""
    content = host.file("/opt/lab-uri-post.json").content_string
    data = json.loads(content)
    # httpbin retourne le body envoye sous "json"
    assert "json" in data
    assert data["json"]["name"] == "rhce"
    assert data["json"]["version"] == 2026
