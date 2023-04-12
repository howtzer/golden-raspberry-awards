from app import app
from unittest import TestCase

class TestIntegrations(TestCase):
    def setUp(self):
        self.app = app.test_client()


    def test_get_200(self):
        response = self.app.get('/get')
        response_expected = {
            "max": [
                {
                "followingWin": 2015,
                "interval": 13,
                "previousWin": 2002,
                "producer": 152
                },
                {
                "followingWin": 1994,
                "interval": 9,
                "previousWin": 1985,
                "producer": 32
                }
            ],
            "min": [
                {
                "followingWin": 1991,
                "interval": 1,
                "previousWin": 1990,
                "producer": 58
                },
                {
                "followingWin": 1990,
                "interval": 6,
                "previousWin": 1984,
                "producer": 28
                }
            ]
            }
        assert response.status == "200 OK"
        assert response.json == response_expected


    def test_post_200(self):
        data = {'producers': 'Jerry Weintraub 23', 'studios': 'Lorimar Productions, United Artists', 'title': 'Cruising', 'winner': '', 'year': 1980}
        response = self.app.post('/post', json=data)
        assert response.status == "200 OK"


    def test_post_500(self):
        data = {}
        response = self.app.post('/post', json=data)
        assert response.status == "500 INTERNAL SERVER ERROR"


    def test_put_200(self):
        data = {
            'producers': 'Jerry Weintraub 23',
            'studios': 'Lorimar Productions, United Artists',
            'title': 'Cruising',
            'winner': '',
            'year': 1980
            }
        response_post = self.app.post('/post', json=data)
        data['id'] = response_post.json['id']
        data['producers'] = 'Outro produtos'
        response_put = self.app.put('/put', json=data)
        assert response_put.status == "200 OK"


    def test_put_500(self):
        data = {}
        response = self.app.put('/put', json=data)
        assert response.status == "500 INTERNAL SERVER ERROR"


    def test_delete_200(self):
        data = {
            'producers': 'Jerry Weintraub 23',
            'studios': 'Lorimar Productions, United Artists',
            'title': 'Cruising',
            'winner': '',
            'year': 1980
            }
        response_post = self.app.post('/post', json=data)
        response_delete = self.app.delete('/delete', json=response_post.json)
        assert response_delete.status == "200 OK"


    def test_delete_500(self):
        data = {}
        response = self.app.delete('/delete', json=data)
        assert response.status == "500 INTERNAL SERVER ERROR"
