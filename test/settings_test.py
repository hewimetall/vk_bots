import unittest
from settings import Setting

class TestSettings(unittest.TestCase):
    def test_init(self):
        setting = Setting()
        self.assertTrue('DEFAULT' in setting.conf)

    # проверка коректности загрузки файла конфигурация
    def test_init_args(self):
        setting = Setting('./conf/settings.ini')
        self.assertTrue('DEFAULT' in setting.conf)

    # проверка коректности загрузки файлов конфигурация из settings.ini
    def test_load_file_ini(self):
        setting = Setting()
        self.assertEqual(len(setting.conf.defaults().keys()), len(setting.config))  # add assertion here
        self.assertEqual(3, len(setting.config))  # Количество файлов

        setting = Setting('./conf/settings.ini')
        self.assertEqual(3, len(setting.config))  # add assertion here

    # проверка коректности загрузки файлов конфигурация по путям из settings.ini
    def test_load_files(self):
        setting = Setting()
        for conf in setting.config.values():
            self.assertTrue(len(conf.sections()) > 0)
        setting = Setting('./conf/settings.ini')
        for conf in setting.config.values():
            self.assertTrue(len(conf.sections()) > 0)


if __name__ == '__main__':
    unittest.main()
