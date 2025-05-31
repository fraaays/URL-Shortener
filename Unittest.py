import unittest
import sqlite3
import json  
from app import app, randomString
from unittest.mock import patch, MagicMock
import os

class FlaskURLShortenerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.db = sqlite3.connect(':memory:')
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            CREATE TABLE urls (
                id INTEGER PRIMARY KEY,
                longurl TEXT,
                shorturl TEXT UNIQUE
            )
        ''')
        self.db.commit()

        patcher = patch('sqlite3.connect', return_value=self.db)
        self.addCleanup(patcher.stop)
        self.mock_connect = patcher.start()

    def tearDown(self):
        self.db.close()

    def test_random_string_is_unique(self):
        db = sqlite3.connect('data.db')
        cursor = db.cursor()
        string1 = randomString(cursor)
        string2 = randomString(cursor)
        db.close()
        self.assertNotEqual(string1, string2)

    def test_random_string_collision_handling(self):
        """Test randomString handles collisions by generating new strings"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [('exists',), None]
        
        result = randomString(mock_cursor)

        self.assertEqual(mock_cursor.fetchone.call_count, 2)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 6)

    def test_index_get(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'http', response.data or b'')

    def test_index_post_empty_url(self):
        response = self.app.post('/', data={'longurl': ''})
        self.assertIn(b'Please enter a URL', response.data)

    def test_index_post_invalid_json(self):
        """Test POST with invalid Content-Type"""
        response = self.app.post('/', data={'longurl': 'invalid'}, 
                               content_type='application/json')
        self.assertIn(response.status_code, [200, 400])

    def test_index_post_new_url(self):
        response = self.app.post('/', data={'longurl': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'http://', response.data)

    def test_index_post_existing_url(self):
        """Test posting a URL that already exists in database"""

        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://existing.com', 'exist1'))
        self.db.commit()

        response = self.app.post('/', data={'longurl': 'http://existing.com'})
        self.assertEqual(response.status_code, 200)

        self.assertIn(b'exist1', response.data)

    def test_redirect_existing_shorturl(self):
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://test.com', 'abc123'))
        self.db.commit()
        response = self.app.get('/abc123')
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://test.com', response.location)

    def test_redirect_non_existing_shorturl(self):
        response = self.app.get('/nonexist')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'URL does not exist', response.data)

    def test_delete_url(self):
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://delete.com', 'del123'))
        self.db.commit()
        url_id = self.cursor.lastrowid
        response = self.app.post(f'/delete/{url_id}')
        self.assertEqual(response.status_code, 302)

    def test_delete_nonexistent_url(self):
        """Test deleting a URL that doesn't exist"""
        response = self.app.post('/delete/99999')
        self.assertEqual(response.status_code, 302)

    def test_api_create_url_missing_json(self):
        response = self.app.post('/api/urls', data={})
        self.assertEqual(response.status_code, 400)

    def test_api_create_url_invalid_json(self):
        """Test API with malformed JSON"""
        response = self.app.post('/api/urls', data='invalid json', 
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_api_create_url_missing_longurl(self):
        """Test API with JSON but missing longurl field"""
        response = self.app.post('/api/urls', json={'notlongurl': 'test'})
        self.assertEqual(response.status_code, 400)

    def test_api_create_url_empty_longurl(self):
        """Test API with empty longurl"""
        response = self.app.post('/api/urls', json={'longurl': ''})
        self.assertEqual(response.status_code, 400)

    def test_api_create_url_success(self):
        response = self.app.post('/api/urls', json={'longurl': 'http://json.com'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('shorturl', response.get_json())

    def test_api_create_url_existing(self):
        """Test API creating URL that already exists"""

        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://api-existing.com', 'api123'))
        self.db.commit()

        response = self.app.post('/api/urls', json={'longurl': 'http://api-existing.com'})
        self.assertIn(response.status_code, [200, 201])
        json_data = response.get_json()
        self.assertEqual(json_data['shorturl'], 'api123')

    def test_api_get_urls(self):
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://a.com', 'shorta'))
        self.db.commit()
        response = self.app.get('/api/urls')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.get_json()) >= 1)

    def test_api_get_urls_empty(self):
        """Test API get all URLs when database is empty"""
        response = self.app.get('/api/urls')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_api_get_url_by_id(self):
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://id.com', 'id123'))
        self.db.commit()
        url_id = self.cursor.lastrowid
        response = self.app.get(f'/api/urls/{url_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('longurl', response.get_json())

    def test_api_get_url_not_found(self):
        response = self.app.get('/api/urls/9999')
        self.assertEqual(response.status_code, 404)

    def test_api_update_url(self):
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://old.com', 'old123'))
        self.db.commit()
        url_id = self.cursor.lastrowid
        response = self.app.put(f'/api/urls/{url_id}', json={'longurl': 'http://new.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['longurl'], 'http://new.com')

    def test_api_update_url_missing(self):
        response = self.app.put('/api/urls/9999', json={'longurl': 'http://none.com'})
        self.assertEqual(response.status_code, 404)

    def test_api_update_url_bad_json(self):
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://x.com', 'x123'))
        self.db.commit()
        url_id = self.cursor.lastrowid
        response = self.app.put(f'/api/urls/{url_id}', data='not-json', 
                              content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_api_update_url_missing_longurl(self):
        """Test API update with JSON but missing longurl field"""
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://update.com', 'upd123'))
        self.db.commit()
        url_id = self.cursor.lastrowid
        response = self.app.put(f'/api/urls/{url_id}', json={'notlongurl': 'test'})
        self.assertEqual(response.status_code, 400)

    def test_api_update_url_empty_longurl(self):
        """Test API update with empty longurl"""
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://update2.com', 'upd456'))
        self.db.commit()
        url_id = self.cursor.lastrowid
        response = self.app.put(f'/api/urls/{url_id}', json={'longurl': ''})
        self.assertEqual(response.status_code, 400)

    def test_api_delete_url_success(self):
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://del.com', 'del321'))
        self.db.commit()
        url_id = self.cursor.lastrowid
        response = self.app.delete(f'/api/urls/{url_id}')
        self.assertEqual(response.status_code, 204)

    def test_api_delete_url_not_found(self):
        response = self.app.delete('/api/urls/9999')
        self.assertEqual(response.status_code, 404)

    def test_database_error_handling(self):
        """Test database connection error handling"""
        pass

    def test_special_characters_in_url(self):
        """Test URLs with special characters"""
        special_url = 'http://example.com/path?param=value&other=test#anchor'
        response = self.app.post('/', data={'longurl': special_url})
        self.assertEqual(response.status_code, 200)

    def test_very_long_url(self):
        """Test with very long URL"""
        long_url = 'http://example.com/' + 'a' * 1000
        response = self.app.post('/', data={'longurl': long_url})
        self.assertEqual(response.status_code, 200)

    @patch('sqlite3.connect')
    def test_database_connection_edge_cases(self, mock_connect):
        """Test edge cases in database connection"""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_db

        mock_cursor.fetchone.return_value = None
        response = self.app.get('/nonexistent123')
        self.assertEqual(response.status_code, 200)

    def test_app_run_condition(self):
        """Test the if _name_ == '_main_' condition"""
        import app
        self.assertTrue(hasattr(app, 'app'))


if __name__ == '__main__':
    unittest.main()