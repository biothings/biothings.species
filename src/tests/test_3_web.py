from biothings.tests.web import BiothingsDataTest


class TestTaxonWeb(BiothingsDataTest):
    host = 't.biothings.io'
    # host = '34.221.9.181'
    prefix = 'v1'

    def test_301_status(self):
        self.request('/status')

    def test_302_status(self):
        self.request('/status', method='HEAD')

    # check in the header if it is production (check the header, tornado, nginx, etc)
    def test_303_static(self):
        self.request('/favicon.ico')

    # check in the header if it is production (check the header, tornado, nginx, etc)
    def test_304_static(self):
        self.request('/robots.txt')
