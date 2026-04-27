"""Tests pytest+testinfra pour le challenge boucles-with-deprecated."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.mark.parametrize("fruit", ["apple", "banana", "cherry"])
def test_withitems_files(host, fruit):
    f = host.file(f"/tmp/withitems-{fruit}.txt")
    assert f.exists, f"/tmp/withitems-{fruit}.txt manquant"


def test_withdict_nginx(host):
    f = host.file("/tmp/withdict-nginx.txt")
    assert f.exists
    assert "80" in f.content_string


def test_withdict_redis(host):
    f = host.file("/tmp/withdict-redis.txt")
    assert f.exists
    assert "6379" in f.content_string
