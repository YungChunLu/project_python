import unittest, requests

class TestServer(unittest.TestCase):
    def test010_assert_place_order(self):
        r = requests.post("http://localhost:8080/orders", json={"origin": ["25.0330", "121.5654"], "destination": ["22.9997", "120.2270"]})
        self.assertEqual(r.status_code, 200)
        self.assertSetEqual(set(r.json().keys()), set(["distance", "id", "status"]))

    def test011_handling_missing_arguments(self):
        r = requests.post("http://localhost:8080/orders", json={"destination": ["0", "0"]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"], "Missing required arguments.")
    
    def test012_handling_wrong_arguments(self):
        r = requests.post("http://localhost:8080/orders", json={"origin": ["0.0.0", "0"], "destination": ["0", "0"]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"], "Invalid coordinates.")
        r = requests.post("http://localhost:8080/orders", json={"origin": ["0", "0", "0"], "destination": ["0", "0"]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"], "Invalid coordinates.")
        r = requests.post("http://localhost:8080/orders", json={"origin": ["0"], "destination": ["0", "0"]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"], "Invalid coordinates.")
    
    def test013_assert_arguments_range(self):
        r = requests.post("http://localhost:8080/orders", json={"origin": ["121.5654", "25.0330"], "destination": ["22.3193", "114.1694"]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"], "Invalid coordinates.")

    def test014_assert_take_order(self):
        r = requests.patch("http://localhost:8080/orders/100", json={"status": "TAKEN"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"], "The order doesn't exist.")
        r = requests.patch("http://localhost:8080/orders/1", json={"status": "TAKEN"})
        self.assertEqual(r.status_code, 200)
        self.assertDictEqual(r.json(), {"status": "SUCCESS"})
        r = requests.patch("http://localhost:8080/orders/1", json={"status": "TAKEN"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"], "Oops! The order has been taken.")

    def test015_assert_get_order_list(self):
        for _ in range(5):
            r = requests.post("http://localhost:8080/orders", json={"origin": ["25.0330", "121.5654"], "destination": ["22.9997", "120.2270"]})
            self.assertEqual(r.status_code, 200)
        r = requests.get("http://localhost:8080/orders", params={"page":0, "limit":5})
        self.assertEqual(len(r.json()), 5)
        r = requests.get("http://localhost:8080/orders", params={"page":1, "limit":5})
        self.assertEqual(len(r.json()), 1)

if __name__ == "__main__":
    unittest.main()