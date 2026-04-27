"""Tests pytest+testinfra pour le challenge any_errors_fatal."""

import pytest

from conftest import lab_host


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def web2():
    return lab_host("web2.lab")


def test_marker_web1(web1):
    f = web1.file("/tmp/anyfatal-web1.lab.txt")
    assert f.exists
    assert "any_errors_fatal OK" in f.content_string


def test_marker_web2(web2):
    f = web2.file("/tmp/anyfatal-web2.lab.txt")
    assert f.exists
    assert "any_errors_fatal OK" in f.content_string
