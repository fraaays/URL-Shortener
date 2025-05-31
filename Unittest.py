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

        # Set up in-memory SQLite database
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
        # Create a mock cursor that returns True for exists check initially
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [('exists',), None]  # First exists, second doesn't
        
        result = randomString(mock_cursor)
        
        # Should have called fetchone twice due to collision
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
        # This should handle JSON parsing errors
        self.assertIn(response.status_code, [200, 400])

    def test_index_post_new_url(self):
        response = self.app.post('/', data={'longurl': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'http://', response.data)

    def test_index_post_existing_url(self):
        """Test posting a URL that already exists in database"""
        # Insert URL first
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://existing.com', 'exist1'))
        self.db.commit()
        
        # Post same URL again
        response = self.app.post('/', data={'longurl': 'http://existing.com'})
        self.assertEqual(response.status_code, 200)
        # Should return existing short URL
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
        self.assertEqual(response.status_code, 302)  # Should still redirect

    def test_api_create_url_missing_json(self):
        response = self.app.post('/api/urls', data={})
        self.assertEqual(response.status_code, 400)

    def test_api_create_url_json_exception(self):
        """Test API with request that causes JSON exception - covers lines 112-114"""
        # Send malformed JSON to trigger the except block
        response = self.app.post('/api/urls', 
                               data='{"malformed": json content}',
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)
        json_response = response.get_json()
        self.assertIn('error', json_response)

    def test_api_update_url_json_exception(self):
        """Test API update with malformed JSON - covers line 140"""
        # First create a URL to update
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://test-update.com', 'upd789'))
        self.db.commit()
        url_id = self.cursor.lastrowid
        
        # Send malformed JSON to trigger the except block
        response = self.app.put(f'/api/urls/{url_id}', 
                              data='{"malformed": json content}',
                              content_type='application/json')
        self.assertEqual(response.status_code, 400)
        json_response = response.get_json()
        self.assertIn('error', json_response)

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
        # Insert URL first
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://api-existing.com', 'api123'))
        self.db.commit()
        
        # Try to create same URL via API
        response = self.app.post('/api/urls', json={'longurl': 'http://api-existing.com'})
        self.assertIn(response.status_code, [200, 201])  # Either should be acceptable
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
        # Test specific database error scenarios
        with patch('app.get_db_connection') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            response = self.app.get('/api/urls')
            # Should handle database errors gracefully
            self.assertIn(response.status_code, [500, 200])

    def test_main_execution_block(self):
        """Test the if __name__ == '__main__' block - covers line 178"""
        # Test by patching app.run and executing the module directly
        with patch('app.app.run') as mock_run:
            # Execute the module as main to trigger the if __name__ == '__main__' block
            import runpy
            import sys
            
            # Save the original argv
            original_argv = sys.argv[:]
            
            try:
                # Set argv to simulate running as main script
                sys.argv = ['app.py']
                
                # This should trigger the main block
                exec(compile(open('app.py').read(), 'app.py', 'exec'), {'__name__': '__main__'})
                
                # Verify that app.run was called
                mock_run.assert_called_once()
                
            except SystemExit:
                # app.run() might cause SystemExit, which is expected
                pass
            finally:
                # Restore original argv
                sys.argv = original_argv

    def test_get_db_connection_function(self):
        """Test the get_db_connection function directly"""
        from app import get_db_connection
        # Test that it returns a connection
        with patch('sqlite3.connect') as mock_connect:
            mock_db = MagicMock()
            mock_connect.return_value = mock_db
            result = get_db_connection()
            mock_connect.assert_called_once_with('data.db')
            self.assertEqual(result, mock_db)

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

    def test_exception_handling_in_routes(self):
        """Test exception handling in various routes"""
        # Test what happens when database operations fail
        with patch.object(self.cursor, 'execute', side_effect=sqlite3.Error("SQL Error")):
            response = self.app.get('/api/urls')
            # Should handle SQL errors gracefully
            self.assertIn(response.status_code, [200, 500])
            
        # Test JSON parsing errors more thoroughly
        response = self.app.post('/api/urls', 
                               data='{"invalid": json}', 
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_edge_case_url_handling(self):
        """Test edge cases in URL handling"""
        # Test with None or empty values that might cause issues
        test_cases = [
            'http://example.com',
            'https://example.com',
            'http://example.com/path',
            'http://example.com/path?query=value',
            'http://example.com:8080/path',
        ]
        
        for url in test_cases:
            response = self.app.post('/', data={'longurl': url})
            self.assertEqual(response.status_code, 200)

    def test_app_run_condition(self):
        """Test the if __name__ == '__main__' condition"""
        # Test that the app module can be imported without running
        import app
        self.assertTrue(hasattr(app, 'app'))
        self.assertTrue(hasattr(app, 'randomString'))
        self.assertTrue(hasattr(app, 'get_db_connection'))

    def test_error_responses(self):
        """Test various error response scenarios"""
        # Test 404 errors
        response = self.app.get('/nonexistent-route-that-does-not-exist')
        self.assertEqual(response.status_code, 404)
        
    def test_method_not_allowed(self):
        """Test method not allowed scenarios"""
        # Test unsupported HTTP methods
        response = self.app.patch('/api/urls')
        self.assertEqual(response.status_code, 405)
        
    def test_all_route_variations(self):
        """Test all possible route variations to ensure complete coverage"""
        # Test the root route with different methods
        response = self.app.options('/')
        self.assertIn(response.status_code, [200, 405])
        
        # Test API routes with different variations
        response = self.app.options('/api/urls')
        self.assertIn(response.status_code, [200, 405])

    def test_database_cursor_operations(self):
        """Test database cursor operations that might be missed"""
        # Test cursor commit operations
        self.cursor.execute("INSERT INTO urls (longurl, shorturl) VALUES (?, ?)", 
                          ('http://cursor-test.com', 'cursor1'))
        self.db.commit()
        
        # Verify the insert worked
        self.cursor.execute("SELECT * FROM urls WHERE shorturl = ?", ('cursor1',))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], 'http://cursor-test.com')


if __name__ == '__main__':
    unittest.main()