import os
import pytest
import configparser

def test_inventory_file_exists():
    assert os.path.isfile("fichiers/hosts.ini"), "Le fichier fichiers/hosts.ini est manquant."

def test_dbservers_group_and_vars():
    config = configparser.ConfigParser(allow_no_value=True, delimiters=('='))
    config.read("fichiers/hosts.ini")

    assert 'dbservers' in config.sections(), "Le groupe [dbservers] est absent."
    assert 'dbservers:vars' in config.sections(), "La section [dbservers:vars] est absente."

    db_hosts = [host for host in config['dbservers']]
    assert len(db_hosts) >= 2, "Il doit y avoir au moins deux hôtes dans [dbservers]."

    vars_section = config['dbservers:vars']
    assert 'db_port' in vars_section, "La variable db_port est absente dans [dbservers:vars]."
    assert vars_section['db_port'] == '5432', "La variable db_port doit être 5432."
    assert 'db_engine' in vars_section, "La variable db_engine est absente dans [dbservers:vars]."
    assert vars_section['db_engine'] == 'postgresql', "La variable db_engine doit être postgresql."
