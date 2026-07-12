from pathlib import Path

from settings import IniConfigParser, Setting, parser_ini


def test_parser_ini_returns_attribute_accessible_config(tmp_path):
    config_file = tmp_path / "sample.ini"
    config_file.write_text("[section]\nvalue = 123\n", encoding="utf-8")

    config = parser_ini(config_file)

    assert isinstance(config, IniConfigParser)
    assert config.section["value"] == "123"


def test_setting_loads_default_files():
    setting = Setting()

    assert "DEFAULT" in setting.conf
    assert setting.conf.defaults()["cmd"] == "./commands.ini"
    assert set(setting.config) == {"cmd", "keyboards", "token"}
    assert setting.commands.text["cmd_start"] == "начать"
    assert setting.keyboard.media["send"] == "отправить новость редакции"
    assert setting.config["token"].sections() == []


def test_setting_accepts_explicit_config_path():
    setting = Setting("./conf/settings.ini")

    assert setting.filename == "./conf/settings.ini"
    assert set(setting.config) == {"cmd", "keyboards", "token"}
    assert setting.commands.info["cmd_start"] == "начать"


def test_setting_path_points_to_conf_directory():
    setting = Setting()

    assert Path(setting.path).name == "conf"
    assert Path(setting.path, "settings.ini").exists()
